from django.urls import path

from core import views


urlpatterns = [
    path("", views.index, name="index"),
    path("signup", views.signup, name="signup" ),
    path("login", views.login, name="login"),
    path("logout", views.logout, name="logout"),

    # day
    path("day", views.day_create, name="day-create"),
    path("day/<int:id>", views.day_get, name="day-get"),
    path("day/list", views.day_list, name="day-list"),

    # tasks
    path("day/<int:id>/tasks", views.task_list, name="task-list"),
    path("day/<int:id>/task", views.task_create, name="task-create"),
    path("task/<int:id>/toggle", views.task_toggle, name="task-toggle")
]
