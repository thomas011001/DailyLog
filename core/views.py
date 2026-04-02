from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.shortcuts import render
from django import forms
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout


@login_required
def index(request):
  return render(request, "core/index.html")

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

def login(request):
  if request.user.is_authenticated:
        return redirect('index')

  if request.method == "POST":
    form = LoginForm(request.POST)
    
    body = request.POST
    username = body.get("username")
    password = body.get("password")

    user = authenticate(request, password=password, username=username)
    if user:
      auth_login(request, user)
      return redirect("index")

    return render(request, "core/login.html", {
      "form": form,
      "errors": "Invalid username or password."
    })
  
  form = LoginForm()
  return render(request, "core/login.html", {
    "form": form
  })

@login_required
def logout(request):
  auth_logout(request)
  return redirect("login")