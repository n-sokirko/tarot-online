import hashlib
import hmac
import json
import urllib.parse

from django.conf import settings
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from apps.users.models import User
from apps.users.serializers import RegisterSerializer, UserSerializer


def _verify_telegram_init_data(init_data: str) -> dict | None:
    """
    Validates Telegram Mini App initData HMAC signature.
    Returns the parsed `user` dict or None if the signature is invalid.

    Telegram spec:
      secret_key = HMAC-SHA256(key="WebAppData", data=bot_token)
      hash       = HMAC-SHA256(key=secret_key, data=sorted_data_check_string)
    """
    try:
        params = dict(urllib.parse.parse_qsl(init_data, strict_parsing=True))
    except Exception:
        return None

    received_hash = params.pop('hash', None)
    if not received_hash:
        return None

    data_check_string = '\n'.join(f'{k}={v}' for k, v in sorted(params.items()))

    secret_key = hmac.new(
        b'WebAppData',
        settings.TELEGRAM_BOT_TOKEN.encode('utf-8'),
        hashlib.sha256,
    ).digest()

    expected_hash = hmac.new(
        secret_key,
        data_check_string.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        return None

    user_str = params.get('user')
    if not user_str:
        return None

    try:
        return json.loads(user_str)
    except (json.JSONDecodeError, ValueError):
        return None


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class GoogleAuthView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        credential = request.data.get('credential')
        if not credential:
            return Response({'error': 'No credential provided.'}, status=status.HTTP_400_BAD_REQUEST)

        client_id = settings.GOOGLE_CLIENT_ID
        if not client_id:
            return Response({'error': 'Google OAuth not configured.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            idinfo = id_token.verify_oauth2_token(
                credential,
                google_requests.Request(),
                client_id,
            )
        except ValueError:
            return Response({'error': 'Invalid Google token.'}, status=status.HTTP_400_BAD_REQUEST)

        email = idinfo.get('email')
        if not email:
            return Response({'error': 'No email in token.'}, status=status.HTTP_400_BAD_REQUEST)

        display_name = idinfo.get('name', '')

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'display_name': display_name,
                'is_active': True,
            },
        )
        if created:
            user.set_unusable_password()
            user.save(update_fields=['password'])

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'created': created,
        }, status=status.HTTP_200_OK)


class TelegramWebAppAuthView(APIView):
    """
    Authenticate a Telegram Mini App user via initData HMAC validation.
    Creates a Django user account linked to the Telegram profile on first login.

    POST /api/v1/auth/telegram-webapp/
    Body: { "init_data": "<Telegram.WebApp.initData string>" }
    Returns: { user, access, refresh }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if not settings.TELEGRAM_BOT_TOKEN:
            return Response(
                {'error': 'Telegram not configured.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        init_data = request.data.get('init_data', '')
        if not init_data:
            return Response(
                {'error': 'init_data is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tg_user = _verify_telegram_init_data(init_data)
        if tg_user is None:
            return Response(
                {'error': 'Invalid initData signature.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tg_id = tg_user.get('id')
        if not tg_id:
            return Response(
                {'error': 'No user id in initData.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        first_name = tg_user.get('first_name', '')
        username = tg_user.get('username', '')

        from apps.telegram_bot.models import TelegramUser

        tg_profile, _ = TelegramUser.objects.get_or_create(
            tg_id=tg_id,
            defaults={'tg_username': username, 'tg_first_name': first_name},
        )

        # Keep profile fields fresh
        update_fields = []
        if tg_profile.tg_username != username:
            tg_profile.tg_username = username
            update_fields.append('tg_username')
        if tg_profile.tg_first_name != first_name:
            tg_profile.tg_first_name = first_name
            update_fields.append('tg_first_name')
        if update_fields:
            tg_profile.save(update_fields=update_fields)

        # Create a Django user if none linked yet
        if not tg_profile.user:
            email = f'tg_{tg_id}@telegram.local'
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'display_name': first_name or f'tg_{tg_id}',
                    'is_active': True,
                },
            )
            if created:
                user.set_unusable_password()
                user.save(update_fields=['password'])
            tg_profile.user = user
            tg_profile.save(update_fields=['user'])

        user = tg_profile.user
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })
