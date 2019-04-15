from .models import Video,Hall
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm

class EditProfileForm(UserChangeForm):

    class Meta:
        model = User
        fields = ('username',)
        exclude = ('password',)

# model based form
class VideoForm(forms.ModelForm):

    class Meta:
        model = Video
        fields = ['url']
        labels = {'url':'YouTube URL'}

class SearchForm(forms.Form):
    search_term = forms.CharField(max_length=255, label='Search for Videos')
