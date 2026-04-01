from django.db import models
from django.contrib.auth.models import User

class Day(models.Model):
  owner = models.ForeignKey(User, on_delete=models.CASCADE)
  title = models.CharField(max_length=50, null=True)
  date = models.DateField()