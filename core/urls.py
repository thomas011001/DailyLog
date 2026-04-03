from django.urls import path

from core import views


urlpatterns = [
    path("", views.index, name="index"),
    path("signup", views.signup, name="signup" ),
    path("login", views.login, name="login"),
    path("logout", views.logout, name="logout"),
    path("day", views.day, name="day"),
    path("day/<int:id>", views.day, name="day-detail"),
]
