from django.db import models
from django.contrib.auth.models import User

class Day(models.Model):
  owner = models.ForeignKey(User, on_delete=models.CASCADE)
  title = models.CharField(max_length=50, null=True)
  date = models.DateField()

  class Meta:
    unique_together = ("owner", "date")

class Task(models.Model):
  day = models.ForeignKey(Day, on_delete=models.CASCADE)
  title = models.CharField(max_length=50)
  is_complete = models.BooleanField(default=False)

  def __str__(self) -> str:
    return f"{self.title}: {self.is_complete}"