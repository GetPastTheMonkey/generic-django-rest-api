import random
import uuid
from datetime import timedelta

from django.db import models
from django.db.models import Q
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

from users.models import User


def verification_token():
    min_value = 10 ** (Verification.TOKEN_LENGTH - 1)
    max_value = (10 ** Verification.TOKEN_LENGTH) - 1
    return random.randint(min_value, max_value)


class Verification(models.Model):
    # Model constants
    TOKEN_LENGTH = 6
    VALIDITY_PERIOD_MINUTES = 10

    # Model fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    email = models.EmailField(null=True, default=None)
    phone_number = PhoneNumberField(null=True, default=None)
    username = models.CharField(max_length=150, null=True, default=None)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, null=True, default=None)
    token = models.PositiveIntegerField(default=verification_token)
    secret = models.UUIDField(unique=True, null=True, default=None)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        # These constraints make sure that exactly one type is set and all other types are null
        constraints = [
            models.CheckConstraint(
                check=Q(phone_number__isnull=False) | Q(email__isnull=False) | Q(username__isnull=False),
                name="at_least_one_type"),
            models.CheckConstraint(check=~(Q(phone_number__isnull=False) & Q(email__isnull=False)),
                                   name="not_both_phone_and_email"),
            models.CheckConstraint(check=~(Q(phone_number__isnull=False) & Q(username__isnull=False)),
                                   name="not_both_phone_and_username"),
            models.CheckConstraint(check=~(Q(email__isnull=False) & Q(username__isnull=False)),
                                   name="not_both_email_and_username"),
        ]

    @classmethod
    def clear_outdated(cls):
        current_timestamp = timezone.now()
        oldest_allowed = current_timestamp - timedelta(minutes=cls.VALIDITY_PERIOD_MINUTES)
        cls.objects.filter(created__lte=oldest_allowed).delete()

    def is_email(self) -> bool:
        return self.email is not None

    def is_phone_number(self) -> bool:
        return self.phone_number is not None

    def is_username(self) -> bool:
        return self.username is not None

    def is_authenticated(self) -> bool:
        return self.user is not None
