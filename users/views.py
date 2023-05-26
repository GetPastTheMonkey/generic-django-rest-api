from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models.functions import Now
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError as ValidationErrorDRF
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT, HTTP_403_FORBIDDEN
from rest_framework.views import APIView

from config.settings import AUTH_COOKIE_KEY
from users.models import User
from users.serializers import LoginSerializer, PrivateUserSerializer, ChangePasswordSerializer, PublicUserSerializer, \
    SignupSerializer, ChangeEmailAddressSerializer, ChangePhoneNumberSerializer, ResetPasswordSerializer
from util.response import StatusResponse, DoesNotExistResponse


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    login_serializer = LoginSerializer(data=request.data)
    login_serializer.is_valid(raise_exception=True)

    user = authenticate(
        username=login_serializer.validated_data["username"],
        password=login_serializer.validated_data["password"]
    )

    if not user:
        return StatusResponse("Invalid credentials", HTTP_403_FORBIDDEN)

    # Get authentication token for user
    token, _ = Token.objects.get_or_create(user=user)

    # Update last login and activity
    user.last_login = Now()
    user.last_activity = Now()
    user.save()
    user.refresh_from_db()
    request.user = user

    # Set cookie and return user data
    user_serializer = PrivateUserSerializer(user, context={"request": request})
    response = Response(user_serializer.data)
    response.set_cookie(key=AUTH_COOKIE_KEY, value=token.key, secure=True, httponly=True, samesite="strict")
    return response


@api_view(["POST"])
def logout(request):
    response = Response(status=HTTP_204_NO_CONTENT)
    response.set_cookie(key=AUTH_COOKIE_KEY, value="", max_age=0, secure=True, httponly=True, samesite="strict")
    return response


@api_view(["POST"])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = request.user

    if not user.check_password(serializer.validated_data["old_password"]):
        return StatusResponse("Password incorrect", HTTP_403_FORBIDDEN)

    try:
        # Check if new password is valid
        validate_password(serializer.validated_data["new_password"], user)
    except ValidationError as err:
        raise ValidationErrorDRF({"password": [y for x in err.error_list for y in x.messages]}) from err

    # Set new password
    user.set_password(serializer.validated_data["new_password"])
    user.save()

    return Response(status=HTTP_204_NO_CONTENT)


@api_view(["POST"])
def change_email_address(request):
    serializer = ChangeEmailAddressSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    user_serializer = PrivateUserSerializer(serializer.instance, context={"request": request})
    return Response(user_serializer.data)


@api_view(["POST"])
def change_phone_number(request):
    serializer = ChangePhoneNumberSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    user_serializer = PrivateUserSerializer(serializer.instance, context={"request": request})
    return Response(user_serializer.data)


@api_view(["POST"])
@permission_classes([AllowAny])
def signup(request):
    serializer = SignupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(status=HTTP_204_NO_CONTENT)


@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password(request):
    serializer = ResetPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(status=HTTP_204_NO_CONTENT)


class MeView(APIView):
    def get(self, request):
        serializer = PrivateUserSerializer(request.user, context={"request": request})
        return Response(serializer.data)

    def patch(self, request):
        serializer = PrivateUserSerializer(request.user, data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@api_view(["GET"])
def user_by_id(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return DoesNotExistResponse("User")

    serializer = PublicUserSerializer(user, context={"request": request})
    return Response(serializer.data)
