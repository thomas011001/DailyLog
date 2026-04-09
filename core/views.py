import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render, get_object_or_404
from django import forms
from django.urls import reverse

from core.models import Day, Task

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
  day = get_object_or_404(Day, id=id, owner=request.user)
  if request.htmx:
    response = render(request, 'partials/day_get.html', {'day': day, "task_form": CreateTaskForm()})
    response["HX-Trigger"] = "dayGet"
    return response

  return render(request, "core/day.html", {"day": day, "form": CreatingDayForm(), "task_form": CreateTaskForm()})

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