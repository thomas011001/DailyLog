from django.db import IntegrityError

from django.test import TestCase
from django.contrib.auth.models import User
from .models import Day, Step
from datetime import date

class StepAutoOrderTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ali", password="pass")
        self.day = Day.objects.create(owner=self.user, date=date.today())

    def test_first_step_order(self):
        new_step = Step(day=self.day, type=Step.WORK)
        new_step.save()
        self.assertEqual(new_step.order, 1)

    def test_subsequent_setp(self):
        for _ in range(3):
            Step(day=self.day, type=Step.WORK).save()

        new_step = Step(day=self.day, type=Step.WORK)
        new_step.save()
        self.assertEqual(new_step.order, 4)

    def test_updating_step(self):
        for _ in range(3):
            Step(day=self.day, type=Step.WORK).save()

        new_step = Step(day=self.day, type=Step.WORK)
        new_step.save()

        new_step.type = Step.BREAK
        new_step.save()

        self.assertEqual(new_step.order, 4)

class DayUniqueUserDate(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ali", password="pass")


    def test_unique_user_date(self):
        Day.objects.create(owner=self.user, date=date.today())
        with self.assertRaises(IntegrityError):
            Day.objects.create(owner=self.user, date=date.today())

class StepUniqueOrderDay(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ali", password="pass")
        self.day = Day.objects.create(owner=self.user, date=date.today())

    def test_unique_order(self):
        with self.assertRaises(IntegrityError):
            Step.objects.bulk_create([Step(day=self.day, type=Step.WORK, order=1), Step(day=self.day, type=Step.BREAK, order=1)])
    