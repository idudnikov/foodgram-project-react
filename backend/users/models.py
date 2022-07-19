from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.contrib.auth.models import UserManager


class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(
        "Имя пользователя", max_length=150, unique=True
    )
    password = models.CharField("Пароль", max_length=128, blank=True)
    email = models.EmailField("Email", unique=True)
    first_name = models.CharField("Имя", max_length=150, blank=True)
    last_name = models.CharField("Фамилия", max_length=150, blank=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "username"

    objects = UserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class Subscription(models.Model):
    """
    Класс, описывающий подписку одного пользователя на другого.
    """
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подпичсик"
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Автор"
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [models.UniqueConstraint(
            fields=["user", "author"],
            name="Нельзя подписываться на одного автора более одного раза"
        )]