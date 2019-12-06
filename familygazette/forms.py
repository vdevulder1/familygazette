from django import forms
from .models import Family, Profile, Comment, Post, Suggestion
from django.contrib.auth.models import User
from datetime import date
from PIL import Image

class LoginForm(forms.Form):
    username = forms.CharField(label="Nom d'utilisateur", max_length=30)
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

class ProfileForm(forms.ModelForm):
    x = forms.FloatField(widget=forms.HiddenInput(), required=False)
    y = forms.FloatField(widget=forms.HiddenInput(), required=False)
    width = forms.FloatField(widget=forms.HiddenInput(), required=False)
    height = forms.FloatField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Profile
        fields = ('avatar', 'birthday', 'generalNewsletter', 'postNewsletter', 'commentNewsletter', 'x', 'y', 'width', 'height')
        widgets = {
            'birthday': forms.SelectDateWidget(years=range(1950,2010))
        }

    def save(self):
        profile = super(ProfileForm, self).save()
        
        if profile.avatar :

            x = self.cleaned_data.get('x')
            y = self.cleaned_data.get('y')
            w = self.cleaned_data.get('width')
            h = self.cleaned_data.get('height')

            image = Image.open(profile.avatar)
            cropped_image = image.crop((x, y, w+x, h+y))
            resized_image = cropped_image.resize((200, 200), Image.ANTIALIAS)
            resized_image.save(profile.avatar.path)

        return profile

class FamilyForm(forms.ModelForm):
    class Meta:
        model = Family
        fields = ('description',)

class PostForm(forms.Form):
    title = forms.CharField(label="Titre", max_length=100)
    photo = forms.ImageField()
    event_date = forms.DateField(initial=date.today ,widget=forms.SelectDateWidget, label="Date de l'évènement")
    families = forms.ModelMultipleChoiceField(queryset=None, widget=forms.CheckboxSelectMultiple, label="Famille(s) avec qui partager ce post", required=True)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(PostForm, self).__init__(*args, **kwargs)

        self.fields['families'].queryset = user.families

class UpdatePostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'photo', 'event_date')
        widgets = {
            'event_date': forms.SelectDateWidget()
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('content',)

class SuggestionForm(forms.ModelForm):
    class Meta:
        model = Suggestion
        fields = ('content',)

class MailForm(forms.Form):
    subject = forms.CharField(label="Sujet", max_length=50, required=True)
    content = forms.CharField(label="Contenu", required=True)

class ConversationForm(forms.Form):
    users = forms.ModelMultipleChoiceField(queryset=None, required=True)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ConversationForm, self).__init__(*args, **kwargs)

        self.fields['users'].queryset = Profile.objects.filter(family__in=user.families).distinct().exclude(user=user.user)

class MessageForm(forms.Form):
    content = forms.CharField(required=True)