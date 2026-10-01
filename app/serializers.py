from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class SignupSerializer(serializers.ModelSerializer):
    """
    Registration serializer. Role is required and restricted to Employer/
    Candidate - never let a public signup form create an Admin account.
    Password is validated with Django's built-in validators and hashed via
    create_user() (never saved in plain text).
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    role = serializers.ChoiceField(choices=[User.Role.EMPLOYER, User.Role.CANDIDATE])

    class Meta:
        model = User
        fields = ["id", "username", "email", "phone", "role", "password"]
        extra_kwargs = {"username": {"required": True}}

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)  # hashes the password - never store it raw
        user.save()  # the post_save signal auto-creates the Employer/Candidate profile
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Logs in with email + password (USERNAME_FIELD="email" on User already
    makes this the default), and adds a couple of useful claims to the
    access token so the frontend doesn't need a separate "who am I" call
    just to know the role.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["email"] = user.email
        return token