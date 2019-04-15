from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django.contrib.auth import authenticate, login, update_session_auth_hash
from .models import Hall, Video
from .forms import VideoForm, SearchForm, EditProfileForm
from django.forms import formset_factory
from django.http import Http404, JsonResponse
from django.forms.utils import ErrorList
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
import urllib
import requests


YOUTUBE_API_KEY = 'AIzaSyC5efsoEqcwz0TQf3M2JsfLeP1jYlI-pTI'


# Create your views here.
def home(request):
    recent_fav = Hall.objects.all().order_by('-id')[:3]
    popular_fav = [Hall.objects.get(pk=1),Hall.objects.get(pk=2)]
    return render(request, 'halls/home.html', {'recent_fav':recent_fav, 'popular_fav':popular_fav})

@login_required
def dashboard(request):
    halls = Hall.objects.filter(user=request.user)
    return render(request, 'halls/dashboard.html', {'halls':halls})

@login_required
def add_video(request, pk):
    VideoFormSet = formset_factory(VideoForm, extra=3)

    form = VideoForm()
    search_form = SearchForm()
    hall = Hall.objects.get(pk=pk)
    # if someone tries to add somdthing and they are not the correct owner
    if not hall.user == request.user:
        raise Http404

    if request.method == 'POST':
        # form validation making the video objects
        form = VideoForm(request.POST)
        if form.is_valid():
            video = Video()
            video.hall = hall
            video.url = form.cleaned_data['url']
            parsed_url = urllib.parse.urlparse(video.url)
            video_id = urllib.parse.parse_qs(parsed_url.query).get('v')
            if video_id:
                video.youtube_id = video_id[0]
                response = requests.get(f'https://www.googleapis.com/youtube/v3/videos?part=snippet&id={ video_id[0] }&key={ YOUTUBE_API_KEY }')
                json = response.json()
                title = json['items'][0]['snippet']['title']
                video.title = title
                video.save()
                return redirect('detail_fav', pk)
            else:
                errors = form._errors.setdefault('url', ErrorList())
                errors.append('The url you entered MUST be from youtube.com')

            # template below
    return render(request, 'halls/add_video.html', {'form':form, 'search_form':search_form, 'hall':hall})

@login_required
def video_search(request):
    search_form = SearchForm(request.GET)
    if search_form.is_valid():
        encoded_search_term = urllib.parse.quote(search_form.cleaned_data['search_term'])
        response = requests.get(f'https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=6&q={ encoded_search_term }&key={ YOUTUBE_API_KEY }')
        return JsonResponse(response.json())
    else:
        return JsonResponse({'error':'unable to validate form'})

class DeleteVideo(LoginRequiredMixin, generic.DeleteView):
    model = Video
    template_name='halls/delete_video.html'
    success_url = reverse_lazy('dashboard')

    def get_object(self):
        video = super(DeleteVideo, self).get_object()
        if not video.hall.user == self.request.user:
            raise Http404
        else:
            return video

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect ('home')
    else:
            form = EditProfileForm(instance=request.user)

    context={'form':form}
    return render(request, 'registration/edit_profile.html', context)

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(data=request.POST, user=request.user)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            return redirect ('home')
    else:
            form = PasswordChangeForm(user=request.user)

    context={'form':form}
    return render(request, 'registration/change_password.html', context)


class SignUp(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('dashboard')
    template_name = 'registration/signup.html'
###################################################
# this function customizes the class and logs
# the user in automatically after they sign up
###################################################
    def form_valid(self, form):
        view = super(SignUp, self).form_valid(form)
        username, password = form.cleaned_data.get('username'), form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        login(self.request, user)
        return view

class CreateFav(LoginRequiredMixin, generic.CreateView):
    model = Hall
    fields = ['title']
    template_name = 'halls/create_fav.html'
    success_url = reverse_lazy('dashboard')
###################################################
# the funciton below connects/saves a user to the title
# hall that the user created, in the admin database
###################################################
    def form_valid(self, form):
        form.instance.user = self.request.user
        super(CreateFav, self).form_valid(form)
        return redirect('dashboard')

class DetailFav(generic.DetailView):
    model = Hall
    template_name='halls/detail_fav.html'

class UpdateFav(LoginRequiredMixin, generic.UpdateView):
    model = Hall
    template_name='halls/update_fav.html'
    fields = ['title']
    success_url = reverse_lazy('dashboard')

    def get_object(self):
        hall = super(UpdateFav, self).get_object()
        if not hall.user == self.request.user:
            raise Http404
        else:
            return hall

class DeleteFav(LoginRequiredMixin, generic.DeleteView):
    model = Hall
    template_name='halls/delete_fav.html'
    success_url = reverse_lazy('dashboard')

    def get_object(self):
        hall = super(DeleteFav, self).get_object()
        if not hall.user == self.request.user:
            raise Http404
        else:
            return hall
