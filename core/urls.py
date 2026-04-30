from django.urls import path

from core import views

app_name = 'core'

urlpatterns = [
    path("", views.index, name="index"),

    # day
    path("new", views.new, name="day-create"),
    path("day/<int:id>", views.day_get, name="day-get"),
    path("day/<int:id>/edit", views.day_update, name="day-update"),
    path("day/<int:id>/delete", views.day_delete, name="day-delete"),
    path("history", views.day_list, name="day-list"),

    # tasks
    path("day/<int:id>/task", views.task_create, name="task-create"),
    path("task/<int:id>/toggle", views.task_toggle, name="task-toggle"),
    path("task/<int:id>/delete", views.task_delete, name="task-delete"),

    # steps
    path("day/<int:id>/steps", views.step_list, name="step-list"),
    path("day/<int:id>/step/break", views.break_step_create, name="break-step-create"),
    path("day/<int:id>/step/work", views.work_step_create, name="focus-step-create"),
    path("step/<int:id>/delete", views.step_delete, name="step-delete"),
    path("step/<int:id>/toggle", views.step_toggle, name="step-toggle"),
    path("session/<int:id>/toggle", views.session_toggle, name="session-toggle"),
    path("step/<int:id>/session", views.session_create, name="session-create"),
    
]

