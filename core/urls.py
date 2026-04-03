from django.urls import path

from core import views


urlpatterns = [
    path("", views.index, name="index"),
    path("signup", views.signup, name="signup" ),
    path("login", views.login, name="login"),
    path("logout", views.logout, name="logout"),
    path("day", views.day_create, name="day-create"),
    path("day/<int:id>", views.day_get, name="day-get"),
]
