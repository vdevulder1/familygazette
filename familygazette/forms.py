from django import forms
from .models import Family, Profile, Comment, Post, Suggestion
from django.contrib.auth.models import User

class LoginForm(forms.Form):
    username = forms.CharField(label="Nom d'utilisateur", max_length=30)
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('avatar', 'newsletter')

class FamilyForm(forms.ModelForm):
    class Meta:
        model = Family
        fields = ('description',)

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'photo')

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('content',)

class SuggestionForm(forms.ModelForm):
    class Meta:
        model = Suggestion
        fields = ('content',)
