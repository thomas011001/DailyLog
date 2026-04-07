from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django import forms
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.urls import reverse


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
        return redirect('core:index')

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
              return HttpResponse(status=204, headers={'HX-Redirect': reverse('account:login')})
            return redirect("account:login")
          
        if request.headers.get('HX-Request'):
            return render(request, 'partials/signup_form.html', {"form": form})

  form = SignUpForm()     
  return render(request, 'account/signup.html', {
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
        return redirect('core:index')

  if request.method == "POST":
    form = LoginForm(request.POST)
    
    if form.is_valid():
      auth_login(request, form.user_cache)
      
      return HttpResponse(status=204, headers={'HX-Redirect': reverse('core:index')})

    return render(request, "partials/login_form.html", {
      "form": form
    })

  form = LoginForm()
  return render(request, "account/login.html", {
    "form": form
  })

@login_required
def logout(request):
  auth_logout(request)
  return redirect("account:login")
