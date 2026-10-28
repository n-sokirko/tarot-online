from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from apps.users.models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    # Optional so existing clients keep working: the website always sends both, and
    # when it does the acceptance is recorded with the wording it was given to.
    accepted_terms = serializers.BooleanField(write_only=True, required=False, default=False)
    terms_version = serializers.CharField(write_only=True, required=False, allow_blank=True,
                                          max_length=16, default='')

    class Meta:
        model = User
        fields = ['email', 'password', 'display_name', 'accepted_terms', 'terms_version']

    def create(self, validated_data):
        accepted = validated_data.get('accepted_terms', False)
        return User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            display_name=validated_data.get('display_name', ''),
            terms_accepted_at=timezone.now() if accepted else None,
            terms_version=validated_data.get('terms_version', '') if accepted else '',
        )


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'display_name', 'locale']
        read_only_fields = ['id', 'email']
