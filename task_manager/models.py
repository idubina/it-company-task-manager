from django.contrib.auth.models import AbstractUser
from django.db import models

from it_company_task_manager.settings import AUTH_USER_MODEL


class TaskType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Position(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Worker(AbstractUser):
    position = models.ForeignKey(Position, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "worker"
        verbose_name_plural = "workers"

    def __str__(self):
        return (
            f"{self.username} "
            f"({self.first_name} {self.last_name}) "
            f"[{self.position.name}]"
        )


class Team(models.Model):
    name = models.CharField(max_length=255, unique=True)
    members = models.ManyToManyField(
        AUTH_USER_MODEL, related_name="teams"
    )

    def __str__(self):
        return self.name
