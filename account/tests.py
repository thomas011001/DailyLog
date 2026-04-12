from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from .views import SignUpForm, LoginForm, UpdateProfileForm, ChangePasswordForm

class SignUpViewTest(TestCase):
    def test_get_signup_page(self):
        res = self.client.get(reverse("account:signup"))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "account/signup.html")

    def test_already_auth_user(self):
        user = User.objects.create_user(username="ali", password="pass")
        self.client.force_login(user)
        res = self.client.get(reverse("account:signup"))
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, reverse("core:index"))

    def test_valid_post_signup(self):
        res = self.client.post(reverse("account:signup"), {
            "first_name": "Bazz",
            "last_name": "Foo",
            "username": "bazzfoo",
            "password": "secret password",
            "confirm_password": "secret password"
        })

        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, reverse("account:login"))

        user = User.objects.get(username="bazzfoo")

        self.assertEqual(user.first_name, "Bazz")
        self.assertEqual(user.last_name, "Foo")
        self.assertTrue(user.check_password("secret password"))

    def test_invalid_post_signup(self):
        res = self.client.post(reverse("account:signup"), {
            "first_name": "Bazz",
            "last_name": "Foo",
            "username": "bazzfoo",
            "password": "secret password",
            "confirm_password": "wrong password"
        })

        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "partials/signup_form.html")

class SignupFormTest(TestCase):
    def test_valid_form(self):
        form = SignUpForm({
            "first_name": "Bazz",
            "last_name": "Foo",
            "username": "bazzfoo",
            "password": "secret password",
            "confirm_password": "secret password"
        })

        self.assertTrue(form.is_valid())

    def test_invalid_username_with_space(self):
        form = SignUpForm({
            "first_name": "Bazz",
            "last_name": "Foo",
            "username": "bazz foo",
            "password": "secret password",
            "confirm_password": "secret password"
        })

        self.assertFalse(form.is_valid())
        self.assertIn("Username can't have spaces", form.errors["username"])

    def test_invalid_username_already_taken(self):
        User.objects.create_user(username="bazzfoo", password="password")
        form = SignUpForm({
            "first_name": "Bazz",
            "last_name": "Foo",
            "username": "bazzfoo",
            "password": "secret password",
            "confirm_password": "secret password"
        })

        self.assertFalse(form.is_valid())
        self.assertIn("This username is already taken, please choose another.", form.errors["username"])
    
    def test_invalid_password_mismatch(self):
        form = SignUpForm({
            "first_name": "Bazz",
            "last_name": "Foo",
            "username": "bazzfoo",
            "password": "secret password",
            "confirm_password": "wrong password"
        })

        self.assertFalse(form.is_valid())
        self.assertIn("Passwords do not match.", form.errors["confirm_password"])
        
class LoginFormTest(TestCase):
    def setUp(self):
        User.objects.create_user(username="bazzfoo", password="secret password")
    
    def test_valid_form(self):
        form = LoginForm({
            "username": "bazzfoo",
            "password": "secret password"
        })

        self.assertTrue(form.is_valid())

    def test_invalid_password_or_password_or_both(self):
        cases = [
            {
                "username": "bazzfoo",
                "password": "wrong password"
            },
            {
                "username": "wrongusername",
                "password": "secret password"
            },
            {
                "username": "wrongusername",
                "password": "wrong password"
            }
        ]

        for case in cases:
            form = LoginForm(case)
            self.assertFalse(form.is_valid())
            self.assertIn("Invalid username or password.", form.errors["__all__"])

class LoginViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="bazzfoo", password="secret password")

    def test_get_login_page(self):
        res = self.client.get(reverse("account:login"))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "account/login.html")

    def test_already_auth_user(self):
        self.client.force_login(self.user)
        res = self.client.get(reverse("account:login"))
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, reverse("core:index"))

    def test_valid_post_login(self):
        res = self.client.post(reverse("account:login"), {
            "username": "bazzfoo",
            "password": "secret password"
        })

        self.assertEqual(res.status_code, 204)
        self.assertEqual(res.headers.get('HX-Redirect'), reverse("core:index"))
        self.assertTrue(self.client.session.get('_auth_user_id'))

    def test_invalid_post_login(self):
        res = self.client.post(reverse("account:login"), {
            "username": "bazzfoo",
            "password": "wrong password"
        })

        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "partials/login_form.html")
        self.assertFalse(self.client.session.get('_auth_user_id'))

class LogoutViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")

    def test_unlogged_user_cannot_access(self):
        res = self.client.get(reverse("account:logout"))
        self.assertEqual(res.status_code, 302)
        self.assertIn(reverse("account:login"), res.url)

    def test_logout_redirects_to_login(self):
        self.client.force_login(self.user)
        res = self.client.get(reverse("account:logout"))
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, reverse("account:login"))
        self.assertFalse(self.client.session.get('_auth_user_id'))

class UpdateProfileFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", first_name="Test", last_name="User")
        self.other_user = User.objects.create_user(username="otheruser", password="password")

    def test_username_no_spaces(self):
        form = UpdateProfileForm({
            "first_name": "Test",
            "last_name": "User",
            "username": "test user"
        }, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("Username can't have spaces", form.errors["username"])

    def test_username_unique(self):
        form = UpdateProfileForm({
            "first_name": "Test",
            "last_name": "User",
            "username": "otheruser"
        }, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("This username is already taken, please choose another.", form.errors["username"])

    def test_valid_profile_update(self):
        form = UpdateProfileForm({
            "first_name": "Updated",
            "last_name": "Name",
            "username": "updatedusername"
        }, instance=self.user)
        self.assertTrue(form.is_valid())

class UpdateProfileViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")

    def test_unlogged_user_cannot_access(self):
        res = self.client.get(reverse("account:update-profile"))
        self.assertEqual(res.status_code, 302)
        self.assertIn(reverse("account:login"), res.url)

    def test_valid_post_update_profile(self):
        self.client.force_login(self.user)
        res = self.client.post(reverse("account:update-profile"), {
            "first_name": "Updated",
            "last_name": "Name",
            "username": "updatedusername"
        })
        self.assertEqual(res.status_code, 204)
        self.assertEqual(res.headers.get('HX-Trigger'), 'profileUpdated')
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "updatedusername")

    def test_invalid_post_update_profile(self):
        self.client.force_login(self.user)
        res = self.client.post(reverse("account:update-profile"), {
            "first_name": "Updated",
            "last_name": "Name",
            "username": "invalid username"
        })
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "partials/settings_profile_form.html")

class ChangePasswordFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="oldpassword")

    def test_password_mismatch(self):
        form = ChangePasswordForm({
            "current_password": "oldpassword",
            "new_password": "newpassword123",
            "confirm_password": "differentpassword"
        }, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("New passwords do not match.", form.errors["__all__"])

    def test_incorrect_current_password(self):
        form = ChangePasswordForm({
            "current_password": "wrongpassword",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123"
        }, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("Incorrect current password.", form.errors["current_password"])

    def test_valid_case(self):
        form = ChangePasswordForm({
            "current_password": "oldpassword",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123"
        }, user=self.user)
        self.assertTrue(form.is_valid())

class ChangePasswordViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="oldpassword")

    def test_unlogged_user_cannot_access(self):
        res = self.client.get(reverse("account:change-password"))
        self.assertEqual(res.status_code, 302)
        self.assertIn(reverse("account:login"), res.url)

    def test_invalid_post_change_password(self):
        self.client.force_login(self.user)
        res = self.client.post(reverse("account:change-password"), {
            "current_password": "wrongpassword",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123"
        })
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "partials/settings_password_form.html")

    def test_valid_post_change_password(self):
        self.client.force_login(self.user)
        res = self.client.post(reverse("account:change-password"), {
            "current_password": "oldpassword",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123"
        })
        self.assertEqual(res.status_code, 204)
        self.assertEqual(res.headers.get('HX-Trigger'), 'passwordChanged')
        
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpassword123"))
        
   