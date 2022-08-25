from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    first_name = models.CharField(
        max_length=200,
        verbose_name="Имя",
    )
    last_name = models.CharField(
        max_length=200,
        verbose_name="Фамилия",
    )
    email = models.EmailField(
        max_length=200,
        unique=True,
        verbose_name="Электронная почта",
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
