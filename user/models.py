from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.utils import timezone

from pdf.models import Pdf


# Customized Django's default User model
# Password is always unusable, user is signed in with Google account
class CustomUser(AbstractBaseUser):
    email = models.EmailField(
        unique=True,
        error_messages={
            "unique": "A user with that email already exists.",
        },
    )
    created_at = models.DateTimeField(
        verbose_name="date joined", default=timezone.now
    )
    last_login = models.DateTimeField(
        verbose_name='last login', default=timezone.now
    )

    pdf = models.OneToOneField(
        Pdf,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="user",
    )

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def save(self, *args, **kwargs):
        self.set_unusable_password()
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        db_table = "user"
