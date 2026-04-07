from django.urls import path

from account import views

app_name = 'account'

urlpatterns = [
    path("signup", views.signup, name="signup"),
    path("login", views.login, name="login"),
    path("logout", views.logout, name="logout"),
    path("profile", views.update_profile, name="update-profile"),
    path("profile-header", views.profile_header_get, name="profile-header-get"),
    path("password", views.change_password, name="change-password"),
]
