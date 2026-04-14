import json
from datetime import date, timedelta

from django.db import IntegrityError
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from .models import Day, Task, Step, WorkSession
from .views import CreatingDayForm, EditingDayForm, CreateTaskForm, CreateBreakStep, CreateWorkStep

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
            Step.objects.bulk_create([
                Step(day=self.day, type=Step.WORK, order=1),
                Step(day=self.day, type=Step.BREAK, order=1),
            ])


class CreatingDayFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="ali", password="pass")
        # A day that already exists — used to test duplicate-date validation
        cls.existing_day = Day.objects.create(owner=cls.user, date=date.today())

    def test_valid_with_title(self):
        tomorrow = date.today() + timedelta(days=1)
        form = CreatingDayForm(data={"title": "My Day", "date": tomorrow}, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_without_title(self):
        """title is optional (required=False)."""
        tomorrow = date.today() + timedelta(days=1)
        form = CreatingDayForm(data={"title": "", "date": tomorrow}, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)

    def test_duplicate_date_rejected(self):
        """A date already used by this user must raise a validation error."""
        form = CreatingDayForm(data={"title": "Duplicate", "date": date.today()}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("date", form.errors)
        self.assertIn("This Day Already Exists.", form.errors["date"])

    def test_duplicate_date_allowed_for_different_user(self):
        """Another user is free to create a day on the same date."""
        other_user = User.objects.create_user(username="bob", password="pass")
        form = CreatingDayForm(data={"title": "Bob's Day", "date": date.today()}, user=other_user)
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_date_invalid(self):
        form = CreatingDayForm(data={"title": "No Date", "date": ""}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("date", form.errors)

# ---------------------------------------------------------------------------
# Form tests — Task and Step Forms
# ---------------------------------------------------------------------------

class CreateTaskFormTest(TestCase):
    def test_valid_task_form(self):
        form = CreateTaskForm(data={"title": "Test Task"})
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_task_form_short_title(self):
        form = CreateTaskForm(data={"title": "A"})
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)


class CreateBreakStepTest(TestCase):
    def test_valid_break_form(self):
        form = CreateBreakStep(data={"description": "Taking a coffee break"})
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_break_form_short_desc(self):
        form = CreateBreakStep(data={"description": "0"})
        self.assertFalse(form.is_valid())
        self.assertIn("description", form.errors)


class CreateWorkStepTest(TestCase):
    def test_valid_work_form(self):
        form = CreateWorkStep(data={"sessions_counter": 4})
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_work_form_zero_sessions(self):
        form = CreateWorkStep(data={"sessions_counter": 0})
        self.assertFalse(form.is_valid())
        self.assertIn("sessions_counter", form.errors)

# ---------------------------------------------------------------------------
# Form tests — EditingDayForm
# ---------------------------------------------------------------------------

class EditingDayFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="ali", password="pass")
        cls.day = Day.objects.create(owner=cls.user, date=date.today(), title="Day 1")
        cls.other_day = Day.objects.create(
            owner=cls.user,
            date=date.today() + timedelta(days=1),
            title="Day 2",
        )

    def test_valid_update_same_date(self):
        """Editing without changing the date must stay valid."""
        form = EditingDayForm(
            data={"title": "Updated Title", "date": date.today()},
            instance=self.day,
            user=self.user,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_update_new_date(self):
        free_date = date.today() + timedelta(days=7)
        form = EditingDayForm(
            data={"title": "New Date", "date": free_date},
            instance=self.day,
            user=self.user,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_duplicate_date_rejected(self):
        """Changing to a date already taken by another Day of the same user fails."""
        taken_date = self.other_day.date
        form = EditingDayForm(
            data={"title": "Clash", "date": taken_date},
            instance=self.day,
            user=self.user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("date", form.errors)
        self.assertIn("This Day Already Exists.", form.errors["date"])

    def test_missing_title_invalid(self):
        form = EditingDayForm(
            data={"title": "", "date": date.today()},
            instance=self.day,
            user=self.user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)


# ---------------------------------------------------------------------------
# View tests — day_create
# ---------------------------------------------------------------------------

class DayCreateViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="ali", password="pass")

    def setUp(self):
        self.client.force_login(self.user)
        self.url = reverse("core:day-create")
        self.tomorrow = date.today() + timedelta(days=1)

    # Auth
    def test_unauthenticated_redirected(self):
        self.client.logout()
        res = self.client.post(self.url, {"title": "X", "date": self.tomorrow})
        self.assertEqual(res.status_code, 302)
        self.assertIn(reverse("account:login"), res.url)

    # GET not allowed (require_POST)
    def test_get_not_allowed(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 405)

    # Valid POST
    def test_valid_post_creates_day(self):
        res = self.client.post(self.url, {"title": "Hello", "date": self.tomorrow})
        self.assertEqual(res.status_code, 204)
        self.assertTrue(Day.objects.filter(owner=self.user, date=self.tomorrow).exists())

    def test_valid_post_returns_htmx_headers(self):
        res = self.client.post(self.url, {"title": "Hello", "date": self.tomorrow})
        trigger = json.loads(res.headers.get("HX-Trigger", "{}"))
        self.assertIn("closeDialog", trigger)
        self.assertIn("dayCreated", trigger)
        location = json.loads(res.headers.get("HX-Location", "{}"))
        self.assertIn("path", location)

    def test_valid_post_without_title(self):
        res = self.client.post(self.url, {"title": "", "date": self.tomorrow})
        self.assertEqual(res.status_code, 204)
        self.assertTrue(Day.objects.filter(owner=self.user, date=self.tomorrow).exists())

    # Invalid POST — duplicate date
    def test_duplicate_date_returns_form(self):
        Day.objects.create(owner=self.user, date=self.tomorrow)
        res = self.client.post(self.url, {"title": "Dupe", "date": self.tomorrow})
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "partials/creating_day_form.html")

    # Invalid POST — missing date
    def test_missing_date_returns_form(self):
        res = self.client.post(self.url, {"title": "No Date"})
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "partials/creating_day_form.html")


# ---------------------------------------------------------------------------
# View tests — day_update
# ---------------------------------------------------------------------------

class DayUpdateViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="ali", password="pass")
        cls.other_user = User.objects.create_user(username="bob", password="pass")

    def setUp(self):
        self.client.force_login(self.user)
        self.day = Day.objects.create(owner=self.user, date=date.today(), title="Original")
        self.url = reverse("core:day-update", kwargs={"id": self.day.pk})
        self.free_date = date.today() + timedelta(days=5)

    # Auth
    def test_unauthenticated_redirected(self):
        self.client.logout()
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 302)
        self.assertIn(reverse("account:login"), res.url)

    def test_wrong_user_gets_404(self):
        self.client.force_login(self.other_user)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 404)

    # GET
    def test_get_renders_edit_form(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "partials/editing_day_form.html")

    # Valid POST
    def test_valid_post_updates_day(self):
        res = self.client.post(self.url, {"title": "Updated", "date": self.free_date})
        self.assertEqual(res.status_code, 204)
        self.day.refresh_from_db()
        self.assertEqual(self.day.title, "Updated")
        self.assertEqual(self.day.date, self.free_date)

    def test_valid_post_returns_htmx_headers(self):
        res = self.client.post(self.url, {"title": "Updated", "date": self.free_date})
        trigger = json.loads(res.headers.get("HX-Trigger", "{}"))
        self.assertIn("closeDialog", trigger)
        self.assertIn("dayCreated", trigger)

    # Invalid POST — duplicate date
    def test_duplicate_date_returns_form(self):
        Day.objects.create(owner=self.user, date=self.free_date)
        res = self.client.post(self.url, {"title": "Clash", "date": self.free_date})
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "partials/editing_day_form.html")

    def test_invalid_post_does_not_update_db(self):
        Day.objects.create(owner=self.user, date=self.free_date)
        self.client.post(self.url, {"title": "Clash", "date": self.free_date})
        self.day.refresh_from_db()
        self.assertEqual(self.day.title, "Original")


# ---------------------------------------------------------------------------
# View tests — day_delete
# ---------------------------------------------------------------------------

class DayDeleteViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="ali", password="pass")
        cls.other_user = User.objects.create_user(username="bob", password="pass")

    def setUp(self):
        self.client.force_login(self.user)
        self.day = Day.objects.create(owner=self.user, date=date.today())
        self.url = reverse("core:day-delete", kwargs={"id": self.day.pk})

    # Auth
    def test_unauthenticated_redirected(self):
        self.client.logout()
        res = self.client.post(self.url)
        self.assertEqual(res.status_code, 302)
        self.assertIn(reverse("account:login"), res.url)

    # GET not allowed
    def test_get_not_allowed(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 405)

    # Wrong user gets 404
    def test_wrong_user_gets_404(self):
        self.client.force_login(self.other_user)
        res = self.client.post(self.url)
        self.assertEqual(res.status_code, 404)

    # Valid delete
    def test_valid_delete_removes_day(self):
        res = self.client.post(self.url)
        self.assertEqual(res.status_code, 204)
        self.assertFalse(Day.objects.filter(pk=self.day.pk).exists())

    def test_valid_delete_returns_hx_redirect(self):
        res = self.client.post(self.url)
        self.assertEqual(res.headers.get("HX-Redirect"), reverse("core:index"))
# ---------------------------------------------------------------------------
# View tests — Tasks
# ---------------------------------------------------------------------------

class TaskViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="ali", password="pass")
        cls.other_user = User.objects.create_user(username="bob", password="pass")
        cls.day = Day.objects.create(owner=cls.user, date=date.today())
        cls.other_day = Day.objects.create(owner=cls.other_user, date=date.today())

    def setUp(self):
        self.client.force_login(self.user)

    def test_task_list_view(self):
        Task.objects.create(day=self.day, title="Task 1")
        Task.objects.create(day=self.day, title="Task 2")
        url = reverse("core:task-list", kwargs={"id": self.day.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "partials/task_list.html")
        self.assertEqual(len(res.context["tasks"]), 2)

    def test_task_create_view_valid(self):
        url = reverse("core:task-create", kwargs={"id": self.day.id})
        res = self.client.post(url, {"title": "New Task"})
        self.assertEqual(res.status_code, 204)
        self.assertTrue(Task.objects.filter(day=self.day, title="New Task").exists())
        self.assertIn("taskCreated", res.headers.get("HX-Trigger"))

    def test_task_create_view_invalid(self):
        url = reverse("core:task-create", kwargs={"id": self.day.id})
        res = self.client.post(url, {"title": "A"}) # too short
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "partials/create_task_form.html")

    def test_task_toggle_view(self):
        task = Task.objects.create(day=self.day, title="Toggle Task", is_complete=False)
        url = reverse("core:task-toggle", kwargs={"id": task.id})
        res = self.client.post(url)
        self.assertEqual(res.status_code, 200)
        task.refresh_from_db()
        self.assertTrue(task.is_complete)
        self.assertTemplateUsed(res, "partials/task_item.html")

    def test_task_delete_view_success(self):
        task = Task.objects.create(day=self.day, title="Delete Task")
        url = reverse("core:task-delete", kwargs={"id": task.id})
        res = self.client.post(url)
        self.assertEqual(res.status_code, 200)
        self.assertFalse(Task.objects.filter(id=task.id).exists())

    def test_task_delete_view_wrong_user(self):
        task = Task.objects.create(day=self.other_day, title="Bob's Task")
        url = reverse("core:task-delete", kwargs={"id": task.id})
        res = self.client.post(url)
        self.assertEqual(res.status_code, 404)

# ---------------------------------------------------------------------------
# View tests — Steps
# ---------------------------------------------------------------------------

class StepViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="ali", password="pass")
        cls.other_user = User.objects.create_user(username="bob", password="pass")
        cls.day = Day.objects.create(owner=cls.user, date=date.today())
        cls.other_day = Day.objects.create(owner=cls.other_user, date=date.today())

    def setUp(self):
        self.client.force_login(self.user)

    def test_step_list_view(self):
        Step.objects.create(day=self.day, type=Step.WORK)
        url = reverse("core:step-list", kwargs={"id": self.day.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "partials/step_list.html")
        self.assertEqual(len(res.context["steps"]), 1)

    def test_break_step_create_valid(self):
        url = reverse("core:break-step-create", kwargs={"id": self.day.id})
        res = self.client.post(url, {"description": "Coffee Break"})
        self.assertEqual(res.status_code, 204)
        self.assertTrue(Step.objects.filter(day=self.day, type=Step.BREAK, description="Coffee Break").exists())
        self.assertIn("stepCreated", res.headers.get("HX-Trigger"))

    def test_work_step_create_valid(self):
        url = reverse("core:work-step-create", kwargs={"id": self.day.id})
        res = self.client.post(url, {"sessions_counter": 3})
        self.assertEqual(res.status_code, 204)
        step = Step.objects.get(day=self.day, type=Step.WORK)
        self.assertEqual(step.sessions.count(), 3)
        self.assertIn("stepCreated", res.headers.get("HX-Trigger"))

    def test_step_toggle_view(self):
        step = Step.objects.create(day=self.day, type=Step.WORK, is_complete=False)
        url = reverse("core:step-toggle", kwargs={"id": step.id})
        res = self.client.post(url)
        self.assertEqual(res.status_code, 200)
        step.refresh_from_db()
        self.assertTrue(step.is_complete)
        self.assertTemplateUsed(res, "partials/step_list.html")

    def test_step_delete_view_success(self):
        step = Step.objects.create(day=self.day, type=Step.BREAK)
        url = reverse("core:step-delete", kwargs={"id": step.id})
        res = self.client.post(url)
        self.assertEqual(res.status_code, 200)
        self.assertFalse(Step.objects.filter(id=step.id).exists())

    def test_step_delete_view_wrong_user(self):
        step = Step.objects.create(day=self.other_day, type=Step.BREAK)
        url = reverse("core:step-delete", kwargs={"id": step.id})
        res = self.client.post(url)
        self.assertEqual(res.status_code, 404)

# ---------------------------------------------------------------------------
# View tests — Sessions
# ---------------------------------------------------------------------------

class SessionViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="ali", password="pass")
        cls.day = Day.objects.create(owner=cls.user, date=date.today())
        cls.step = Step.objects.create(day=cls.day, type=Step.WORK)

    def setUp(self):
        self.client.force_login(self.user)

    def test_session_toggle_view(self):
        session = WorkSession.objects.create(step=self.step, is_complete=False)
        url = reverse("core:session-toggle", kwargs={"id": session.id})
        res = self.client.post(url)
        self.assertEqual(res.status_code, 200)
        session.refresh_from_db()
        self.assertTrue(session.is_complete)
        self.assertTemplateUsed(res, "partials/step_list.html")

    def test_session_create_view(self):
        url = reverse("core:session-create", kwargs={"id": self.step.id})
        res = self.client.post(url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.step.sessions.count(), 1)
        self.assertTemplateUsed(res, "partials/step_list.html")

# ---------------------------------------------------------------------------
# View tests — Day Detail & Header
# ---------------------------------------------------------------------------

class DayDetailViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="ali", password="pass")
        cls.day = Day.objects.create(owner=cls.user, date=date.today())

    def setUp(self):
        self.client.force_login(self.user)

    def test_day_get_full_page(self):
        url = reverse("core:day-get", kwargs={"id": self.day.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "core/day.html")

    def test_day_get_htmx(self):
        url = reverse("core:day-get", kwargs={"id": self.day.id})
        res = self.client.get(url, HTTP_HX_REQUEST="true")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "partials/day_get.html")
        self.assertEqual(res.headers.get("HX-Trigger"), "dayGet")

    def test_day_header_view(self):
        url = reverse("core:day-header", kwargs={"id": self.day.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "cotton/dayHeader.html")
        self.assertEqual(res.context["day"], self.day)
