from phonenumber_field.phonenumber import PhoneNumber
from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault

from verification.models import Verification


class VerificationRequestSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=CurrentUserDefault())

    class Meta:
        model = Verification
        fields = ["phone_number", "email", "username", "user"]

    def __init__(self, *args, **kwargs):
        Verification.clear_outdated()
        super().__init__(*args, **kwargs)

    @staticmethod
    def validate_phone_number(value):
        if value is None:
            return value

        phone_number = PhoneNumber.from_string(value)

        if not phone_number.is_valid():
            raise serializers.ValidationError("Phone number is invalid")

        # Remove all previous verification processes for this phone number
        Verification.objects.filter(phone_number=phone_number).delete()

        return phone_number

    @staticmethod
    def validate_email(value):
        # Remove all previous verification processes for this email address
        Verification.objects.filter(email=value).delete()
        return value

    @staticmethod
    def validate_username(value):
        # Remove all previous verification processes for this username
        Verification.objects.filter(username=value).delete()
        return value

    @staticmethod
    def validate_user(value):
        if value.is_authenticated:
            return value
        else:
            return None

    def validate(self, attrs):
        attributes = 0

        for a in ["phone_number", "email", "username"]:
            if a in attrs and attrs[a] is not None:
                attributes += 1

        if attributes == 0:
            raise serializers.ValidationError("Empty type submitted - not allowed")
        elif attributes != 1:
            raise serializers.ValidationError("More than one type submitted")

        return attrs

    def create(self, validated_data):
        # TODO: Actually send verification token via out-of-band channel
        v = super().create(validated_data)  # type: Verification
        print(v.token)
        return v

    def update(self, instance, validated_data):
        raise NotImplementedError("Not allowed to call update")


class VerificationConfirmSerializer(serializers.Serializer):
    verification = serializers.UUIDField()
    token = serializers.IntegerField(min_value=10 ** (Verification.TOKEN_LENGTH - 1),
                                     max_value=(10 ** Verification.TOKEN_LENGTH) - 1)

    def __init__(self, *args, **kwargs):
        Verification.clear_outdated()
        super().__init__(*args, **kwargs)
