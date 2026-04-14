---
name: django-testing
description: >
  A complete guide for testing Django apps using Django's built-in TestCase framework.
  Use this skill whenever the user wants to write tests for a Django app, test models,
  forms, views, authentication, HTMX responses, or any Django-specific behavior.
  Trigger this skill for prompts like "test my django app", "how do I write django tests",
  "test my views", "test my models", "test my forms", or any variation of writing,
  running, or organizing tests in a Django project.
---

# Django Testing Skill

## Core Concepts

### How Django Isolates Tests
Django does NOT mock the database. It creates a **real separate database** (`test_<your_db_name>`), runs all migrations, then **wraps each test in a transaction that gets rolled back** after the test finishes. This means:
- Each test starts with a clean slate automatically
- No manual cleanup needed
- The test DB is dropped entirely when the suite finishes
- Use `--keepdb` flag to skip recreating the DB between runs (faster when migrations haven't changed)

### Test Discovery
Django only runs methods prefixed with `test_`. Methods without this prefix are silently ignored — a common gotcha.

### setUp vs setUpTestData
- `setUp()` — runs before **every** test method. Use when tests modify shared data.
- `setUpTestData()` — runs **once** for the whole class. Use for read-only shared data. Much faster.

```python
class MyTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="ali", password="pass")  # runs once
    
    def setUp(self):
        self.client.force_login(self.user)  # runs before every test
```

---

## Testing Order (The Pyramid)

Test in this order — each layer builds on the last:

1. **Models** → custom logic, constraints
2. **Forms** → validation logic (forms hold most business rules in FBV Django apps)
3. **Views** → scenarios/outcomes (not logic — that's already tested in forms/models)

---

## 1. Model Tests

**Rule: Test behavior YOU wrote, not behavior Django wrote.**

Test:
- Custom `save()` or `clean()` methods ✅
- Custom model methods ✅
- `unique_together` / critical DB constraints ✅
- Custom managers or querysets ✅

Skip:
- `CharField(max_length=50)` enforcing 50 chars ❌ (Django's job)
- ForeignKey cascade deletes ❌ (Django's job)
- `__str__` returning a string ❌ (too trivial)

### Common Pitfall: bulk_create
`bulk_create` bypasses the model's `save()` method entirely. If your model has custom `save()` logic, use a loop instead:

```python
# WRONG — bypasses custom save()
Step.objects.bulk_create([Step(...), Step(...)])

# RIGHT — calls save() on each
for _ in range(3):
    Step(day=self.day, type=Step.WORK).save()
```

However, `bulk_create` IS useful when you deliberately want to bypass `save()` — e.g., testing DB-level constraints directly.

### Testing unique_together
```python
def test_unique_order(self):
    with self.assertRaises(IntegrityError):
        Step.objects.bulk_create([
            Step(day=self.day, type=Step.WORK, order=1),
            Step(day=self.day, type=Step.BREAK, order=1)
        ])
```

---

## 2. Form Tests

Test forms directly without going through views. Instantiate with data and call `is_valid()`:

```python
form = MyForm(data={"field": "value"})
self.assertTrue(form.is_valid())
```

### Where errors live
- Field-level errors (from `clean_<fieldname>()`): `form.errors["fieldname"]`
- Form-level errors (from `clean()`): `form.errors["__all__"]`

### Use subTest for multiple invalid cases
```python
def test_invalid_cases(self):
    cases = [
        {"username": "ali", "password": "short"},
        {"username": "ali", "password": "pass1", "confirm_password": "pass2"},
    ]
    for data in cases:
        with self.subTest(data=data):
            form = MyForm(data)
            self.assertFalse(form.is_valid())
```

### Always test both valid AND invalid
A valid test case confirms your form isn't accidentally rejecting everything.

---

## 3. View Tests

Use `self.client` — Django's built-in test client (equivalent to FastAPI's TestClient).

### Authentication
```python
self.client.force_login(user)   # simulate logged-in user (no password needed)
```

### Checking sessions
```python
self.assertTrue(self.client.session.get('_auth_user_id'))   # user is logged in
self.assertFalse(self.client.session.get('_auth_user_id'))  # user is not logged in
```

### View Test Checklist
For every view, think through these dimensions:

| Dimension | Cases to cover |
|---|---|
| **Auth** | unauthenticated, wrong user, correct user |
| **HTTP method** | GET, POST |
| **Form state** | valid data, invalid data |
| **Response type** | full page, partial, redirect, HTMX header |

### Standard assertions
```python
self.assertEqual(res.status_code, 200)
self.assertTemplateUsed(res, "myapp/page.html")
self.assertRedirects(res, reverse("myapp:some-view"))

# For HTMX responses (HX-Redirect, HX-Trigger etc.)
self.assertEqual(res.status_code, 204)
self.assertEqual(res.headers.get('HX-Redirect'), reverse("core:index"))
self.assertEqual(res.headers.get('HX-Trigger'), 'someEvent')
```

### Verifying DB changes
After a POST that modifies the DB, always call `refresh_from_db()`:
```python
self.user.refresh_from_db()
self.assertEqual(self.user.username, "newusername")
```

### Unauthenticated access to @login_required views
```python
def test_unauthenticated_cannot_access(self):
    res = self.client.get(reverse("myapp:protected-view"))
    self.assertEqual(res.status_code, 302)
    self.assertIn(reverse("account:login"), res.url)
```

---

## 4. HTMX-Specific Testing

HTMX requests send an `HX-Request: true` header. Your views may behave differently for HTMX vs regular requests. Test both:

```python
# Regular request
res = self.client.post(reverse("myapp:create"), data)

# HTMX request
res = self.client.post(
    reverse("myapp:create"),
    data,
    HTTP_HX_REQUEST="true"
)
```

For HTMX-only responses (204 + HX-Redirect instead of 302):
```python
self.assertEqual(res.status_code, 204)
self.assertEqual(res.headers.get('HX-Redirect'), reverse("core:index"))
```

---

## File Organization

```
myapp/
└── tests.py         # or split into tests/ package

tests/
├── __init__.py
├── test_models.py
├── test_forms.py
└── test_views.py
```

Group related tests into classes:
```python
class StepAutoOrderTest(TestCase): ...
class DayUniqueConstraintTest(TestCase): ...
class SignUpFormTest(TestCase): ...
class SignUpViewTest(TestCase): ...
```

---

## Running Tests

```bash
python manage.py test myapp              # run all tests in app
python manage.py test myapp -v 2         # verbose output
python manage.py test --keepdb           # skip DB recreation (faster)
python manage.py test myapp.tests.test_models  # run specific file
```

---

## Quick Reference: What Goes Where

| Thing to test | Where to test it |
|---|---|
| Custom `save()` logic | Model test |
| `unique_together` | Model test |
| Form field validation | Form test |
| Cross-field validation (`clean()`) | Form test |
| View returns correct template | View test |
| View redirects correctly | View test |
| View rejects unauthenticated users | View test |
| HTMX response headers | View test |
| DB actually updated after POST | View test (with `refresh_from_db`) |
| Every validation edge case | Form test (NOT view test) |