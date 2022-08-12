from django.contrib.auth.models import AbstractUser
from django.db import models
from users.validators import username_validator


class User(AbstractUser):
    username = models.CharField(
        'Логин',
        max_length=150,
        unique=True,
        null=False,
        validators=[username_validator]
    )
    email = models.EmailField('email', unique=True, null=False, max_length=254)
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    REQUIRED_FIELDS = ['username',
                       'first_name',
                       'last_name']

    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.username
