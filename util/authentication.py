from django.db.models.functions import Now
from django.http import HttpRequest
from rest_framework import authentication, exceptions

from config.settings import AUTH_COOKIE_KEY
from users.models import User


class CookieAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request: HttpRequest):
        token = request.COOKIES.get(AUTH_COOKIE_KEY, None)

        if token is None:
            return None

        try:
            user = User.objects.get(auth_token=token)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed("No user with this token")

        # Set last activity to NOW() and resolve NOW() call in DB
        user.last_activity = Now()
        user.save()
        user.refresh_from_db()

        return user, user.auth_token
