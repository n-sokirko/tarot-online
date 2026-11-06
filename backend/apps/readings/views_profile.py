"""The person's tarologist settings: persona, style mirroring, memory, dossier."""
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing import services as billing
from apps.readings import personalization
from apps.readings.models import Interpretation, TarotProfile

PERSONAS = [
    {'key': 'classic', 'premium': False, 'adult': False,
     'name_ru': 'Классика', 'tagline_ru': 'спокойный разбор, как сейчас',
     'name_en': 'Classic', 'tagline_en': 'calm reading, as now'},
    {'key': 'mira', 'premium': True, 'adult': False,
     'name_ru': 'Мира', 'tagline_ru': 'тёплая, как подруга-психолог',
     'name_en': 'Mira', 'tagline_en': 'warm, like a therapist friend'},
    {'key': 'val', 'premium': True, 'adult': False,
     'name_ru': 'Вэл', 'tagline_ru': 'дерзкая, прямая, с юмором',
     'name_en': 'Val', 'tagline_en': 'bold, direct, funny'},
    {'key': 'val18', 'premium': True, 'adult': True,
     'name_ru': 'Вэл 18+', 'tagline_ru': 'без цензуры, с матом',
     'name_en': 'Val 18+', 'tagline_en': 'uncensored, swears'},
    {'key': 'agata', 'premium': True, 'adult': False,
     'name_ru': 'Агата', 'tagline_ru': 'мистическая, говорит образами',
     'name_en': 'Agata', 'tagline_en': 'mystic, speaks in images'},
]
_KEYS = {p['key']: p for p in PERSONAS}


def _payload(profile: TarotProfile, premium: bool) -> dict:
    return {
        'persona': profile.persona,
        'effective_persona': personalization.effective_persona(profile, premium),
        'mirror_style': profile.mirror_style,
        'remember': profile.remember,
        'adult_confirmed': bool(profile.adult_confirmed_at),
        'dossier': profile.dossier or [],
        'premium': premium,
        'personas': PERSONAS,
    }


class TarologistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = personalization.get_profile(request.user)
        premium = billing.tier_for(request.user).tier != 'free'
        return Response(_payload(profile, premium))

    def patch(self, request):
        profile = personalization.get_profile(request.user)
        premium = billing.tier_for(request.user).tier != 'free'
        data = request.data
        fields = []

        if data.get('adult_confirm') is True and not profile.adult_confirmed_at:
            profile.adult_confirmed_at = timezone.now()
            fields.append('adult_confirmed_at')

        if 'persona' in data:
            key = data.get('persona')
            meta = _KEYS.get(key)
            if meta is None:
                return Response({'detail': 'unknown_persona'}, status=status.HTTP_400_BAD_REQUEST)
            if meta['premium'] and not premium:
                return Response({'detail': 'premium_required'}, status=status.HTTP_402_PAYMENT_REQUIRED)
            if meta['adult'] and not profile.adult_confirmed_at:
                return Response({'detail': 'adult_confirmation_required'},
                                status=status.HTTP_400_BAD_REQUEST)
            profile.persona = key
            fields.append('persona')

        if 'mirror_style' in data:
            want = bool(data.get('mirror_style'))
            if want and not premium:
                return Response({'detail': 'premium_required'}, status=status.HTTP_402_PAYMENT_REQUIRED)
            profile.mirror_style = want
            fields.append('mirror_style')

        if 'remember' in data:
            profile.remember = bool(data.get('remember'))
            fields.append('remember')

        if 'dossier' in data:
            if not isinstance(data.get('dossier'), list):
                return Response({'detail': 'dossier must be a list'}, status=status.HTTP_400_BAD_REQUEST)
            profile.dossier = personalization.clean_dossier(data['dossier'])
            fields.append('dossier')

        if fields:
            profile.save(update_fields=[*fields, 'updated_at'])
        return Response(_payload(profile, premium))


class TarologistForgetView(APIView):
    """«Стереть всё»: the dossier and every reading memo go; readings stay."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = personalization.get_profile(request.user)
        profile.dossier = []
        profile.save(update_fields=['dossier', 'updated_at'])
        Interpretation.objects.filter(reading__user=request.user).exclude(memo='').update(memo='')
        premium = billing.tier_for(request.user).tier != 'free'
        return Response(_payload(profile, premium))
