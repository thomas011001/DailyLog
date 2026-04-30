import json

from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render, get_object_or_404
from django import forms
from django.urls import reverse
from django_htmx.http import trigger_client_event

from core.models import Day, Task, Step, WorkSession

class EditingDayForm(forms.ModelForm):
  class Meta:
    model = Day
    fields = ['title', 'date']
    widgets = {
      'date': forms.DateInput(attrs={"type": "date"})
    }

  def __init__(self, *args, **kwargs):
    self.user = kwargs.pop('user', None)
    super(EditingDayForm, self).__init__(*args, **kwargs)

  def clean_date(self):
    date = self.cleaned_data.get('date')
    if self.user and Day.objects.filter(owner=self.user, date=date).exclude(pk=self.instance.pk).exists():
      raise forms.ValidationError("This Day Already Exists.")
    return date


class CreatingDayForm(forms.Form):
  title = forms.CharField(label="Title", max_length=50, min_length=1, required=False, widget=forms.TextInput(attrs={"placeholder": "New Day Title"}))
  date = forms.DateField(label="Date", widget=forms.DateInput(attrs={"type": "date", "x-ref": "dateInput"}))

  def __init__(self, *args, **kwargs):
    self.user = kwargs.pop('user', None)
    super(CreatingDayForm, self).__init__(*args, **kwargs)

  def clean_date(self):
    date = self.cleaned_data.get('date')
        
    if self.user and Day.objects.filter(owner=self.user, date=date).exists():
      raise forms.ValidationError("This Day Already Exists.")
            
    return date

class CreateTaskForm(forms.Form):
  title = forms.CharField(min_length=2)

class CreateBreakStep(forms.Form):
  description = forms.CharField(label="Description",min_length=2)

class CreateWorkStep(forms.Form):
  sessions_counter = forms.IntegerField(label="Number of Sessions",min_value=1)

@login_required
def index(request):
  if request.htmx:
    return render(request, "core/index.html#page")
  return render(request, "core/index.html",)

def day_list(request):
  days = Day.objects.filter(owner=request.user).order_by("-date")
  paginator = Paginator(days, 5)

  page_number = request.GET.get("page")  
  page = paginator.get_page(page_number)

  context = {"days": page.object_list, "has_next": page.has_next(), "has_previous": page.has_previous() , "page_number": page.number, "next": page.number + 1, "previous": page.number - 1}

  if request.htmx:
    return render(request, "core/history.html#page", context)
  return render(request, "core/history.html", context)


@login_required
def day_update(request, id):
    day = get_object_or_404(Day, id=id, owner=request.user)
    
    if request.method == "POST":
        form = EditingDayForm(request.POST, instance=day, user=request.user)
        if form.is_valid():
            form.save()
            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps({
                        "closeDialog": None,
                        "refreshDayList": None, 
                    }),
                    "HX-Location": json.dumps({
                        "path": reverse("core:day-get", kwargs={'id': day.pk}),
                        "target": "#day-content",
                        "swap": "outerHTML",
                    })
                }
            )
    else:
        form = EditingDayForm(instance=day)

    return render(request, 'partials/editing_day_form.html', {"form": form, "day": day})

@require_POST
@login_required
def day_delete(request, id):
    day = get_object_or_404(Day, id=id, owner=request.user)
    day.delete()
    return HttpResponse(
        status=204,
        headers={
            "HX-Location": json.dumps({
                          "path": reverse("core:index"),
                          "target": "#day-content",
                          "swap": "outerHTML",
                      })
        }
    )
    
def day_get(request, id):
  day = get_object_or_404(Day.objects.prefetch_related('task_set', "steps__sessions"), pk=id)
  print(day.steps.all)
  context = {"day": day, "tasks": day.task_set.all(), "steps": day.steps.all()}
  if request.htmx:
    return render(request, 'core/day.html#page', context)

  return render(request, "core/day.html", context)


def task_create(request, id):
  day = get_object_or_404(Day, pk=id)
  form = CreateTaskForm(request.POST)
  if form.is_valid():
    data = form.cleaned_data

    new_task = Task(day=day, title=data["title"])
    new_task.save()

    return render(request, "core/day.html#task", {"task": new_task})
  
  return HttpResponse("")

@require_POST
def task_toggle(request, id):
  task = get_object_or_404(Task, pk=id)
  task.is_complete = not task.is_complete
  print(task.is_complete)
  task.save()
  
  return HttpResponse(status=204)

@require_POST
@login_required
def task_delete(request, id):
    task = get_object_or_404(Task, pk=id, day__owner=request.user)
    task.delete()
    return HttpResponse("")


@require_POST
@login_required
def break_step_create(request, id):
  form = CreateBreakStep(request.POST)
  if form.is_valid():
    data = form.cleaned_data

    new_step = Step(day_id=id, type=Step.BREAK, description=data["description"])
    new_step.save()
  
    return render(request, "core/day.html#step", {"step": new_step})
  
  return render(request, "partials/create_break_step_form.html", {"form": form, "dayid": id})

@require_POST
@login_required
def work_step_create(request, id):
  form = CreateWorkStep(request.POST)
  if form.is_valid():
    data = form.cleaned_data

    new_step = Step(day_id=id, type=Step.WORK)
    new_step.save()
    work_sessions = [WorkSession(step=new_step) for _ in range(data["sessions_counter"])]
    new_step.sessions.bulk_create(work_sessions)

    return render(request, "core/day.html#step", {"step": new_step})
  
  return render(request, "partials/create_work_step_form.html", {"dayid": id, "form": form})

def step_list(request, id):
  steps = Step.objects.prefetch_related("sessions").filter(day_id=id)
  return render(request, "cotton/step_list.html", {"steps": steps})
    

@require_POST
@login_required
def step_delete(request, id):
    step = get_object_or_404(Step, pk=id, day__owner=request.user)
    step.delete()
    return HttpResponse("")

@require_POST
@login_required
def step_toggle(request, id):
    step = get_object_or_404(Step, pk=id, day__owner=request.user)
    step.is_complete = not step.is_complete
    step.save()
    
    return HttpResponse(status=204)

@require_POST
@login_required
def session_toggle(request, id):
    session = get_object_or_404(WorkSession, pk=id, step__day__owner=request.user)
    session.is_complete = not session.is_complete
    session.save()
    
    return HttpResponse(status=204)
@require_POST
@login_required
def session_create(request, id):
    step = get_object_or_404(Step, pk=id, day__owner=request.user)
    WorkSession.objects.create(step=step)
    
    steps = Step.objects.prefetch_related("sessions").filter(day_id=step.day_id)
    return render(request, "partials/step_list.html", {"steps": steps})

@login_required
def new(request):
  if request.method == "POST":
    form = CreatingDayForm(request.POST, user=request.user)
    if form.is_valid():
      data = form.cleaned_data
      new_day = Day(owner=request.user, title=data["title"], date=data["date"])
      new_day.save()
      
      return HttpResponse(
                  status=204,
                  headers={
                      "HX-Location": json.dumps({
                          "path": reverse("core:day-get", kwargs={'id': new_day.pk}),
                          "target": "#page-content",
                          "swap": "innerHTML",
                      })
                  }
              )

    return render(request, "core/new.html#form", {"form": form})
  
  form = CreatingDayForm()
  if request.htmx:
    return render(request, "core/new.html#page", {"form": form})
    

  return render(request, "core/new.html", {"form": form})


@require_POST
@login_required
def day_create(request):
    form = CreatingDayForm(request.POST, user=request.user)
    
    if form.is_valid():
      data = form.cleaned_data

      new_day = Day(owner=request.user, title=data["title"], date=data["date"])
      new_day.save()
  
      return HttpResponse(
                  status=204,
                  headers={
                      "HX-Trigger": json.dumps({
                          "closeDialog": None,
                          "refreshDayList": None, 
                      }),
                      "HX-Location": json.dumps({
                          "path": reverse("core:day-get", kwargs={'id': new_day.pk}),
                          "target": "#day-content",
                          "swap": "outerHTML",
                      })
                  }
              )

    return render(request, 'partials/creating_day_form.html', {"form": form})
