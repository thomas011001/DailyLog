from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.shortcuts import render
from django import forms
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.urls import is_valid_path, reverse

from core.models import Day


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

@login_required
def index(request):
  return render(request, "core/index.html", context)

@login_required
def day(request):
  if request.method == "POST":
    form = CreatingDayForm(request.POST, user=request.user)
    
    if form.is_valid():
      data = form.cleaned_data

      new_day = Day(owner=request.user, title=data["title"], date=data["date"])
      new_day.save()
      if request.htmx:
        return HttpResponse(status=204, headers={'HX-Redirect': reverse('index')})
    if request.headers.get('HX-Request'):
      return render(request, 'partials/creating_day_form.html', {"form": form})

  return HttpResponse("")

class SignUpForm(forms.Form):
  first_name = forms.CharField(label="First Name", max_length=50, min_length=2)
  last_name = forms.CharField(label="Last Name", max_length=50, min_length=2)
  username = forms.CharField(label="Username",max_length=50, min_length=3)
  password = forms.CharField(label="Password", widget=forms.PasswordInput(), min_length=8)

  def clean_username(self):
    username = self.cleaned_data["username"]
    if " " in username: 
      raise forms.ValidationError("Username can't have spaces")
    
    if User.objects.filter(username=username).exists():
      raise forms.ValidationError("This username is already taken, please choose another.")

    return username

def signup(request):
  if request.user.is_authenticated:
        return redirect('index')

  if request.method == "POST":
        form = SignUpForm(request.POST)
        
        if form.is_valid():
            data = form.cleaned_data
            
            new_user = User.objects.create_user(
                username=data["username"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                password=data["password"]
            )
            if request.htmx:
              return HttpResponse(status=204, headers={'HX-Redirect': reverse('login')})
            return redirect("login")
          
        if request.headers.get('HX-Request'):
            return render(request, 'partials/signup_form.html', {"form": form})

  form = SignUpForm()     
  return render(request, 'core/signup.html', {
    "form": form,
  })

class LoginForm(forms.Form):
  username = forms.CharField(label="Username", required=True)
  password = forms.CharField(label="Password",widget=forms.PasswordInput() , required=True)
  
  def clean(self):
    cleaned_data = super().clean()
    username = cleaned_data.get('username')
    password = cleaned_data.get('password')

    if username and password:
      user = authenticate(username=username, password=password)
      if user is None:
        raise forms.ValidationError("Invalid username or password.")
    
      self.user_cache = user
      
    return cleaned_data
  
def login(request):
  if request.user.is_authenticated:
        return redirect('index')

  if request.method == "POST":
    form = LoginForm(request.POST)
    
    if form.is_valid():
      auth_login(request, form.user_cache)
      
      return HttpResponse(status=204, headers={'HX-Redirect': reverse('login')})

    return render(request, "partials/login_form.html", {
      "form": form
    })

  form = LoginForm()
  return render(request, "core/login.html", {
    "form": form
  })

@login_required
def logout(request):
  auth_logout(request)
  return redirect("login")