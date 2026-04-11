import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render, get_object_or_404
from django import forms
from django.urls import reverse

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
  title = forms.CharField(label="Title", max_length=50, min_length=1, required=False)
  date = forms.DateField(label="Date", widget=forms.DateInput(attrs={"type": "date"}))

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
  context = {
    "form": CreatingDayForm()
  }
  return render(request, "core/index.html", context)

def day_list(request):
  days = Day.objects.filter(owner=request.user).order_by("-date")
  return render(request, "partials/day_list.html", {"days": days})

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
                          "dayCreated": None, 
                      }),
                      "HX-Location": json.dumps({
                          "path": reverse("core:day-get", kwargs={'id': new_day.pk}),
                          "target": "#day-content",
                          "swap": "outerHTML",
                      })
                  }
              )

    return render(request, 'partials/creating_day_form.html', {"form": form})

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
                        "dayCreated": None, 
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
            "HX-Redirect": reverse("core:index")
        }
    )
    
def day_get(request, id):
  if request.htmx:
    response = render(request, 'partials/day_get.html', {'dayid':id, "task_form": CreateTaskForm(), "break_step_form": CreateBreakStep(), "work_step_form": CreateWorkStep()})
    response["HX-Trigger"] = "dayGet"
    return response

  return render(request, "core/day.html", {"dayid":id, "form": CreatingDayForm(), "task_form": CreateTaskForm(), "break_step_form": CreateBreakStep(), "work_step_form": CreateWorkStep()})

def day_header(request, id):
  day = get_object_or_404(Day, id=id, owner=request.user)
  return render(request, "cotton/dayHeader.html", {"day": day})

def task_list(request, id):
  tasks = Task.objects.filter(day_id=id)
  return render(request, "partials/task_list.html", {"tasks": tasks})

def task_create(request, id):
  day = get_object_or_404(Day, pk=id)
  form = CreateTaskForm(request.POST)
  if form.is_valid():
    data = form.cleaned_data

    new_task = Task(day=day, title=data["title"])
    new_task.save()

    return HttpResponse(
                  status=204,
                  headers={
                      "HX-Trigger": json.dumps({
                          "closeDialog": None,
                          "taskCreated": None, 
                      }),
                  }
               ) 
  
  return render(request, "partials/create_task_form.html", {"day": day, "task_form": form})

@require_POST
def task_toggle(request, id):
  task = get_object_or_404(Task, pk=id)
  task.is_complete = not task.is_complete
  print(task.is_complete)
  task.save()
  
  return render(request, "partials/task_item.html", {"task": task})

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
  
    return HttpResponse(
                  status=204,
                  headers={
                      "HX-Trigger": json.dumps({
                          "closeDialog": None,
                          "stepCreated": None, 
                      }),
                  }
               ) 
  
  return render(request, "partials/create_break_step_form.html", {"day": day, "form": form})

@require_POST
@login_required
def work_step_create(request, id):
  form = CreateWorkStep(request.POST)
  if form.is_valid():
    data = form.cleaned_data

    new_step = Step(day_id=id, type=Step.WORK)
    new_step.save()
    work_session = [WorkSession(step=new_step) for _ in range(data["sessions_counter"])]
    WorkSession.objects.bulk_create(work_session)
  
    return HttpResponse(
                  status=204,
                  headers={
                      "HX-Trigger": json.dumps({
                          "closeDialog": None,
                          "stepCreated": None, 
                      }),
                  }
               ) 
  
  return render(request, "partials/create_work_step_form.html", {"day": day, "form": form})

def step_list(request, id):
  steps = Step.objects.prefetch_related("sessions").filter(day_id=id)
  return render(request, "partials/step_list.html", {"steps": steps})
    

@require_POST
@login_required
def step_delete(request, id):
    step = get_object_or_404(Step, pk=id, day__owner=request.user)
    day_id = step.day_id
    step.delete()
    # After deleting, we might want to refresh the list or just return nothing if handled by htmx delete
    return HttpResponse("")

@require_POST
@login_required
def step_toggle(request, id):
    step = get_object_or_404(Step, pk=id, day__owner=request.user)
    step.is_complete = not step.is_complete
    step.save()
    
    # We need to render the step list again or just the single step?
    # Since step_list.html iterates over steps, rendering it again is easier if we have the day_id
    steps = Step.objects.prefetch_related("sessions").filter(day_id=step.day_id)
    return render(request, "partials/step_list.html", {"steps": steps})

@require_POST
@login_required
def session_toggle(request, id):
    session = get_object_or_404(WorkSession, pk=id, step__day__owner=request.user)
    session.is_complete = not session.is_complete
    session.save()
    
    # Refresh the step list to show updated session state
    steps = Step.objects.prefetch_related("sessions").filter(day_id=session.step.day_id)
    return render(request, "partials/step_list.html", {"steps": steps})

@require_POST
@login_required
def session_create(request, id):
    step = get_object_or_404(Step, pk=id, day__owner=request.user)
    WorkSession.objects.create(step=step)
    
    steps = Step.objects.prefetch_related("sessions").filter(day_id=step.day_id)
    return render(request, "partials/step_list.html", {"steps": steps})
