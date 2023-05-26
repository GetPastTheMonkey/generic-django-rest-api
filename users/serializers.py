from typing import Optional

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault

from users.models import User
from verification.models import Verification


class PublicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "date_joined",
            "last_login",
            "last_activity",
            "is_staff",
        ]


class PrivateUserSerializer(serializers.ModelSerializer):
    address_country = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "date_joined",
            "last_login",
            "last_activity",
            "is_staff",
            "address_street_1",
            "address_street_2",
            "address_zip_code",
            "address_town",
            "address_country",
            "email",
            "phone_number",
        ]
        read_only_fields = [
            "id",
            "date_joined",
            "last_login",
            "last_activity",
            "is_staff",
            "email",
            "phone_number",
        ]

    @staticmethod
    def get_address_country(user: User) -> Optional[str]:
        return user.address_country.name if user.address_country and user.address_country.code else None


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()


class ChangeEmailAddressSerializer(serializers.Serializer):
    user = serializers.HiddenField(default=CurrentUserDefault())
    secret = serializers.UUIDField()

    def validate_secret(self, value):
        Verification.clear_outdated()

        try:
            verification = Verification.objects.get(secret=value)
        except Verification.DoesNotExist:
            raise serializers.ValidationError("Invalid secret")

        if not verification.is_email():
            raise serializers.ValidationError("Secret must be from an email verification")

        if not verification.is_authenticated():
            raise serializers.ValidationError("Secret must be from an authenticated verification")

        if verification.user != self.context["request"].user:
            raise serializers.ValidationError("User mismatch")

        if User.objects.filter(email=verification.email).exists():
            raise serializers.ValidationError("Email address already in use")

        return value

    def create(self, validated_data):
        verification = Verification.objects.get(secret=validated_data["secret"])
        user = verification.user
        user.email = verification.email
        user.save()
        verification.delete()
        return user

    def update(self, instance, validated_data):
        raise NotImplementedError("This method should never be called")


class ChangePhoneNumberSerializer(serializers.Serializer):
    user = serializers.HiddenField(default=CurrentUserDefault())
    secret = serializers.UUIDField()

    def validate_secret(self, value):
        Verification.clear_outdated()

        try:
            verification = Verification.objects.get(secret=value)
        except Verification.DoesNotExist:
            raise serializers.ValidationError("Invalid secret")

        if not verification.is_phone_number():
            raise serializers.ValidationError("Secret must be from a phone verification")

        if not verification.is_authenticated():
            raise serializers.ValidationError("Secret must be from an authenticated verification")

        if verification.user != self.context["request"].user:
            raise serializers.ValidationError("User mismatch")

        if User.objects.filter(phone_number=verification.phone_number).exists():
            raise serializers.ValidationError("Phone number already in use")

        return value

    def create(self, validated_data):
        verification = Verification.objects.get(secret=validated_data["secret"])
        user = verification.user
        user.phone_number = verification.phone_number
        user.save()
        verification.delete()
        return user

    def update(self, instance, validated_data):
        raise NotImplementedError("This method should never be called")


class SignupSerializer(serializers.ModelSerializer):
    secret = serializers.UUIDField()

    class Meta:
        model = User
        fields = ["username", "password", "first_name", "last_name", "secret"]

    @staticmethod
    def validate_username(value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already registered")

        return value

    @staticmethod
    def validate_password(value):
        try:
            validate_password(password=value)
        except ValidationError as e:
            raise serializers.ValidationError([y for x in e.error_list for y in x.messages]) from e

        return value

    @staticmethod
    def validate_secret(value):
        Verification.clear_outdated()

        try:
            verification = Verification.objects.get(secret=value)
        except Verification.DoesNotExist:
            raise serializers.ValidationError("Invalid secret")

        if not verification.is_email():
            raise serializers.ValidationError("Secret must be from an email verification")

        if verification.is_authenticated():
            raise serializers.ValidationError("Secret must be from an unauthenticated verification")

        if User.objects.filter(email=verification.email).exists():
            raise serializers.ValidationError("Email address already in use")

        return value

    def create(self, validated_data):
        verification = Verification.objects.get(secret=validated_data["secret"])

        user = User.objects.create_user(
            username=validated_data["username"],
            email=verification.email,
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"]
        )

        verification.delete()

        return user

    def update(self, instance, validated_data):
        raise NotImplementedError("This method should never be called")


class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(validators=[validate_password])
    secret = serializers.UUIDField()

    @staticmethod
    def validate_secret(value):
        Verification.clear_outdated()

        try:
            verification = Verification.objects.get(secret=value)
        except Verification.DoesNotExist:
            raise serializers.ValidationError("Invalid secret")

        if verification.is_authenticated():
            raise serializers.ValidationError("Secret must be from an unauthenticated verification")

        return value

    def create(self, validated_data):
        verification = Verification.objects.get(secret=validated_data["secret"])

        if verification.is_email():
            user = User.objects.get(email=verification.email)
        elif verification.is_phone_number():
            user = User.objects.get(phone_number=verification.phone_number)
        elif verification.is_username():
            user = User.objects.get(username=verification.username)
        else:
            raise NotImplementedError("Invalid program path - unknown verification type")

        user.set_password(validated_data["password"])
        user.save()

        verification.delete()

        return user

    def update(self, instance, validated_data):
        raise NotImplementedError("This method should never be called")
