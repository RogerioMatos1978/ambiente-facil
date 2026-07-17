from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "papel",
            "telefone",
            "departamento",
            "ativo_institucional",
            "is_active",
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined"]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "papel",
            "telefone",
            "departamento",
            "password",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class MeuTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer de login que embute papel e nome no payload do token."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["papel"] = user.papel
        token["nome"] = user.get_full_name() or user.username
        token["is_admin"] = user.is_admin
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["usuario"] = UserSerializer(self.user).data
        return data
