from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django import forms
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.urls import reverse
from django.contrib import messages

class SignUpForm(forms.Form):
  first_name = forms.CharField(label="First Name", max_length=50, min_length=2, widget=forms.TextInput(attrs={"placeholder": "John"}))
  last_name = forms.CharField(label="Last Name", max_length=50, min_length=2, widget=forms.TextInput(attrs={"placeholder": "Doe"}))
  username = forms.CharField(label="Username",max_length=50, min_length=3, widget=forms.TextInput(attrs={"placeholder": "johndoe"}))
  password = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={"placeholder": "Enter your password"}), min_length=8)
  confirm_password = forms.CharField(label="Confirm Password", widget=forms.PasswordInput(attrs={"placeholder": "Confirm your password"}), min_length=8)

  def clean_username(self):
    username = self.cleaned_data["username"]
    if " " in username: 
      raise forms.ValidationError("Username can't have spaces")
    
    if User.objects.filter(username=username).exists():
      raise forms.ValidationError("This username is already taken, please choose another.")

    return username
  
  def clean(self):
    cleaned_data = super().clean()
    password = cleaned_data.get('password')
    confirm_password = cleaned_data.get('confirm_password')

    if password and confirm_password and password != confirm_password:
      self.add_error('confirm_password', "Passwords do not match.")    
    return cleaned_data

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
  username = forms.CharField(label="Username", required=True, widget=forms.TextInput(attrs={"placeholder": "Enter your username"}))
  password = forms.CharField(label="Password",widget=forms.PasswordInput(attrs={"placeholder": "Enter your password"}) , required=True)
  
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
      
      messages.success(request, "You have successfuly logged in.")
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

class UpdateProfileForm(forms.ModelForm):
  class Meta:
    model = User
    fields = ['first_name', 'last_name', 'username']

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields['first_name'].required = True
    self.fields['last_name'].required = True

  def clean_username(self):
    username = self.cleaned_data['username']
    if ' ' in username:
      raise forms.ValidationError("Username can't have spaces")
    if User.objects.exclude(pk=self.instance.pk).filter(username=username).exists():
      raise forms.ValidationError("This username is already taken, please choose another.")
    return username

class ChangePasswordForm(forms.Form):
  current_password = forms.CharField(label="Current Password", widget=forms.PasswordInput())
  new_password = forms.CharField(label="New Password", widget=forms.PasswordInput(), min_length=8)
  confirm_password = forms.CharField(label="Confirm Password", widget=forms.PasswordInput(), min_length=8)

  def __init__(self, *args, **kwargs):
    self.user = kwargs.pop('user', None)
    super().__init__(*args, **kwargs)

  def clean_current_password(self):
    current_password = self.cleaned_data.get('current_password')
    if not self.user.check_password(current_password):
      raise forms.ValidationError("Incorrect current password.")
    return current_password

  def clean(self):
    cleaned_data = super().clean()
    new_password = cleaned_data.get('new_password')
    confirm_password = cleaned_data.get('confirm_password')

    if new_password and confirm_password and new_password != confirm_password:
      raise forms.ValidationError("New passwords do not match.")
    return cleaned_data

@login_required
def update_profile(request):
  if request.method == "POST":
    form = UpdateProfileForm(request.POST, instance=request.user)
    if form.is_valid():
      form.save()
      return HttpResponse(status=204, headers={'HX-Trigger': 'profileUpdated'})
    return render(request, "partials/settings_profile_form.html", {"profile_form": form})
  
  form = UpdateProfileForm(instance=request.user)
  return render(request, "partials/settings_profile_form.html", {"profile_form": form})

@login_required
def change_password(request):
  if request.method == "POST":
    form = ChangePasswordForm(request.POST, user=request.user)
    if form.is_valid():
      request.user.set_password(form.cleaned_data['new_password'])
      request.user.save()
      auth_login(request, request.user) # Keep user logged in
      return HttpResponse(status=204, headers={'HX-Trigger': 'passwordChanged'})
    return render(request, "partials/settings_password_form.html", {"password_form": form})
  
  form = ChangePasswordForm(user=request.user)
  return render(request, "partials/settings_password_form.html", {"password_form": form})

@login_required
def profile_header_get(request):
  return render(request, "partials/profile_header.html")
