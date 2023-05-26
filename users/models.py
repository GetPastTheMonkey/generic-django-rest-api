import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Contact Information
    email = models.EmailField(null=False, unique=True, blank=False)
    phone_number = PhoneNumberField(null=True, default=None)

    # Address
    address_street_1 = models.CharField(max_length=256, null=True, default=None)
    address_street_2 = models.CharField(max_length=256, null=True, default=None)
    address_zip_code = models.CharField(max_length=256, null=True, default=None)
    address_town = models.CharField(max_length=256, null=True, default=None)
    address_country = CountryField(null=True, default=None)

    # Activity tracker
    last_activity = models.DateTimeField(null=False, auto_now_add=True)
