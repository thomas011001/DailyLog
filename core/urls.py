from django.urls import path

from core import views

app_name = 'core'

urlpatterns = [
    path("", views.index, name="index"),

    # day
    path("day", views.day_create, name="day-create"),
    path("day/<int:id>", views.day_get, name="day-get"),
    path("day/<int:id>/edit", views.day_update, name="day-update"),
    path("day/<int:id>/delete", views.day_delete, name="day-delete"),
    path("day/list", views.day_list, name="day-list"),

    # tasks
    path("day/<int:id>/tasks", views.task_list, name="task-list"),
    path("day/<int:id>/task", views.task_create, name="task-create"),
    path("task/<int:id>/toggle", views.task_toggle, name="task-toggle"),
    path("task/<int:id>/delete", views.task_delete, name="task-delete")
]

