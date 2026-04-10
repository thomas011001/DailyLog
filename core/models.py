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

class Step(models.Model):
    WORK = 'work'
    BREAK = 'break'
    TYPE_CHOICES = [
        (WORK, 'Work'),
        (BREAK, 'Break'),
    ]

    day         = models.ForeignKey(Day, on_delete=models.CASCADE, related_name='steps')
    type        = models.CharField(max_length=10, choices=TYPE_CHOICES)
    order       = models.PositiveIntegerField()
    is_complete = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ('day', 'order')
        ordering = ['order']

    def __str__(self):
        return f"Day {self.day.date} | Step {self.order} | {self.type}"


class WorkSession(models.Model):
    step        = models.ForeignKey(Step, on_delete=models.CASCADE, related_name='sessions')
    is_complete = models.BooleanField(default=False)

    def __str__(self):
        return f"Step {self.step.order} | Session {self.order}"
