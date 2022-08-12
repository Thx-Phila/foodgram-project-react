from django.core.validators import RegexValidator


def username_validator(value):
    return RegexValidator(r'^[\w.@+-]+\z', 'Не верное имя пользователя.')
