from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.views.generic import ListView, DeleteView
from django.contrib.auth.decorators import login_required
from .models import Family, Post, Comment, Profile, Suggestion, Gazette
from .forms import LoginForm, UserForm, ProfileForm, PostForm, UpdatePostForm, CommentForm, SuggestionForm
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST, require_GET
from django.core.paginator import Paginator
from django.core import mail
from django.template.loader import render_to_string, get_template
from django.template import RequestContext
from django.utils.html import strip_tags
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseForbidden
from django.conf import settings
import xlwt, zipfile, os
from django.core.files.storage import FileSystemStorage
from PIL import Image

def handler400(request, exception):
    statusCode = 400
    return render(request, 'error-page.html', locals())

def handler403(request, exception):
    statusCode = 403
    return render(request, 'error-page.html', locals())

def handler404(request, exception):
    statusCode = 404
    return render(request, 'error-page.html', locals())

def handler500(request):
    statusCode = 500
    return render(request, 'error-page.html', locals())

def logIn(request):
    """Login page"""
    error = False

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(username=username, password=password)  # Nous vérifions si les données sont correctes
            if user:  # Si l'objet renvoyé n'est pas None
                login(request, user)  # nous connectons l'utilisateur
            else: # sinon une erreur sera affichée
                error = True
    else:
        form = LoginForm()

    return render(request, 'login.html', locals())

def logOut(request):
    logout(request)
    return redirect(reverse(logIn))

@login_required
def home(request):
    """Page d'accueil"""

    return render(request, 'home.html')

class ListPosts(LoginRequiredMixin, ListView):
    model = Post
    context_object_name = "posts"
    template_name = "family.html"
    paginate_by = 3 # attribut de pagination

    def get_queryset(self):
        return Post.objects.filter(family__id=self.kwargs['familyId'])

    def get_context_data(self, **kwargs):
        # Nous récupérons le contexte depuis la super-classe
        context = super(ListPosts, self).get_context_data(**kwargs)
        context['family'] = get_object_or_404(Family, id=self.kwargs['familyId']) 
        return context

class ListMembers(LoginRequiredMixin, ListView):
    model = Profile
    context_object_name = "profiles"
    template_name = "profiles.html"

    def get_queryset(self):
        return get_object_or_404(Family, id=self.kwargs['familyId']).members.all()

    def get_context_data(self, **kwargs):
        context = super(ListMembers, self).get_context_data(**kwargs)
        context['family'] = get_object_or_404(Family, id=self.kwargs['familyId'])
        return context

@login_required
def my_profile(request):
    profile = get_object_or_404(Profile, id=request.user.profile.id)

    return render(request, 'profile.html', {'profile': profile})

@login_required
def get_profile(request, profileId):

    if profileId == request.user.profile.id :
        return redirect('myProfile')

    profile = get_object_or_404(Profile, id=profileId)

    return render(request, 'profile.html', {'profile': profile})

@login_required
def update_profile(request):
    error = False

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            avatarHasChanged = False
            if 'avatar' in profile_form.changed_data :
                avatarHasChanged = True
                get_object_or_404(Profile, id=request.user.profile.id).avatar.delete()
            user_form.save()
            profile_form.save()

            if avatarHasChanged:
                profile = get_object_or_404(Profile, id=request.user.profile.id)
                if profile.avatar :
                    profile.compressAvatar()

            return redirect(my_profile)
        else:
            error = True
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)
    return render(request, 'profile-update.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'error': error
    })

@login_required
def create_post(request, familyId):
    error = False
    posted =  False

    if request.method == 'POST':
        posted = True

    form = PostForm(request.POST or None, request.FILES or None, user=request.user.profile)
    
    if form.is_valid():
        families = form.cleaned_data['families']
        for family in families :
            selected_family = get_object_or_404(Family, id=family.id)
            new_post = Post()
            new_post.title = form.cleaned_data['title']
            new_post.photo = form.cleaned_data['photo']
            new_post.user = request.user.profile
            new_post.family = selected_family
            new_post.save()

            new_post.compressImage()

            for member in selected_family.members.all().exclude(user=request.user) :
                if member.newsletter and member.user.email :
                    subject = 'Nouveau post pour la famille ' + selected_family.name
                    content = 'Nouveau post : \'{0}\' par {1}'.format(new_post.title, request.user.username)
                    context = {
                        'subject': subject,
                        'content': content,
                        'url': 'family/' + str(selected_family.id)
                    }
                    html_message = render_to_string('mail.html', context)
                    plain_message = strip_tags(html_message)
                    mail.send_mail(
                        subject,
                        plain_message,
                        settings.EMAIL_HOST_USER,
                        [member.user.email],
                        html_message=html_message
                    )

        return redirect('family', familyId=familyId)
    else:
        error = True
    
    return render(request, 'new-post.html', locals())

@login_required
def update_post(request, postId):
    error = False
    posted = False
    post = get_object_or_404(Post, id=postId)

    if request.user.profile == post.user :
        if request.method == 'POST':
            posted = True
            form = UpdatePostForm(request.POST, request.FILES, instance=post)
            if form.is_valid():
                photoHasChanged = False
                if 'photo' in form.changed_data :
                    photoHasChanged = True
                    get_object_or_404(Post, id=postId).photo.delete()
                form.save()

                if photoHasChanged:
                    post_ = get_object_or_404(Post, id=postId)
                    if post_.photo :
                        post_.compressImage()

                return redirect('family', familyId=post.family.id)
            else:
                error = True
        else:
            form = UpdatePostForm(instance=post)
        return render(request, 'new-post.html', {
            'form': form,
            'postId': postId,
            'error': error
        })
    else :
        return HttpResponseForbidden("Action Forbidden.")

@login_required
@require_POST
def delete_post(request, postId):

    post = get_object_or_404(Post, id=postId)
    familyId = post.family.id
    post.photo.delete()
    post.delete()

    return redirect('family', familyId=familyId)

@login_required
@require_POST
def create_comment(request, familyId, postId):
    error = False

    form = CommentForm(request.POST or None)
    if form.is_valid():
        selected_post = get_object_or_404(Post, id=postId)
        past_comments = selected_post.comments
        new_comment = Comment()
        new_comment.content = form.cleaned_data['content']
        new_comment.user = request.user.profile
        new_comment.post = selected_post
        new_comment.save()
        
        if selected_post.user.user != request.user and selected_post.user.newsletter and selected_post.user.user.email :
            subject = 'Nouveau commentaire de ' + request.user.username
            content = 'Nouveau commentaire sur votre photo \'{0}\''.format(selected_post.title)
            context = {
                'subject': subject,
                'content': content,
                'url': 'family/' + str(selected_post.family.id)
            }
            html_message = render_to_string('mail.html', context)
            plain_message = strip_tags(html_message)
            mail.send_mail(
                subject,
                plain_message,
                settings.EMAIL_HOST_USER,
                [selected_post.user.user.email],
                html_message=html_message
            )

        users_who_commented = Profile.objects.filter(comment__post=selected_post).distinct().exclude(user=request.user)
        if users_who_commented :
            messages = []
            for user in users_who_commented :
                if user.newsletter and user.user.email :
                    subject = 'Nouveau commentaire de ' + request.user.username
                    content = '{0} a également commenté la photo \'{1}\''.format(request.user.username, selected_post.title)
                    context = {
                        'subject': subject,
                        'content': content,
                        'url': 'family/' + str(selected_post.family.id)
                    }
                    html_message = render_to_string('mail.html', context)
                    plain_message = strip_tags(html_message)
                    mail.send_mail(
                        subject,
                        plain_message,
                        settings.EMAIL_HOST_USER,
                        [user.user.email],
                        html_message=html_message
                    )

        return redirect('family', familyId=familyId)
    else:
        error = True
        return redirect('family', familyId=familyId)
    
@login_required
@require_POST
def delete_comment(request, familyId, commentId):

    get_object_or_404(Comment, id=commentId).delete()

    return redirect('family', familyId=familyId)

class ListSuggestions(LoginRequiredMixin, ListView):
    model = Suggestion
    context_object_name = "suggestions"
    template_name = "suggestions.html"

    def get_queryset(self):
        return Suggestion.objects.all()


@login_required
@require_POST
def create_suggestion(request):
    error = False

    form = SuggestionForm(request.POST or None)
    if form.is_valid():
        new_suggestion = Suggestion()
        new_suggestion.content = form.cleaned_data['content']
        new_suggestion.user = request.user.profile
        new_suggestion.save()
        subject = 'New suggestion from ' + request.user.username
        content = 'New suggestion : ' + new_suggestion.content
        context = {
            'subject': subject,
            'content': content,
            'url': 'suggestions'
        }
        html_message = render_to_string('mail.html', context)
        plain_message = strip_tags(html_message)
        mail.send_mail(
            subject,
            plain_message,
            settings.EMAIL_HOST_USER,
            [Profile.objects.get(user__username='vdevulder').user.email],
            html_message=html_message
        )
        return redirect('suggestions')
    else:
        error = True
        return redirect('suggestions')

@login_required
@require_POST
def like_suggestion(request, suggestionId):
    sugg = get_object_or_404(Suggestion, id=suggestionId)
    user = request.user.profile
    if user in sugg.likes.all() :
        sugg.likes.remove(user)
    else :
        sugg.likes.add(user)

    return redirect('suggestions')

@staff_member_required
def generate_gazette(request, familyId):
    posts = Post.objects.filter(family__id=familyId)
    family = get_object_or_404(Family, id=familyId)

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Posts Data') # this will make a sheet named Posts Data

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    rows = []
    column = ['title', 'user', 'filename']
    files = []
    #column.append('family')
    #row.append(family.name)
    for num,post in enumerate(posts) :
        file_name = post.photo.path.split('/')[-1]
        rows.append([post.title, '{0} {1}'.format(post.user.user.first_name, post.user.user.last_name), file_name])
        files.append(file_name)

    for col_num in range(len(column)):
        ws.write(row_num, col_num, column[col_num], font_style) # at 0 row 0 column 

    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

    wb.save('media/photos/familygazetteExcel.xls')

    response = HttpResponse(content_type='application/zip')
    zf = zipfile.ZipFile(response, 'w')
    zf.write('media/photos/familygazetteExcel.xls')
    for filename in files:
        zf.write(os.path.join('media/photos', filename)) 

    response['Content-Disposition'] = 'attachment; filename=familygazette_{}.zip'.format(family.name)

    os.remove("media/photos/familygazetteExcel.xls")
    
    return response

class ListGazettes(LoginRequiredMixin, ListView):
    model = Gazette
    context_object_name = "gazettes"
    template_name = "gazettes.html"
    paginate_by = 5 # attribut de pagination

    def get_queryset(self):
        return Gazette.objects.filter(family__id=self.kwargs['familyId'])

    def get_context_data(self, **kwargs):
        # Nous récupérons le contexte depuis la super-classe
        context = super(ListGazettes, self).get_context_data(**kwargs)
        context['family'] = get_object_or_404(Family, id=self.kwargs['familyId']) 
        return context

@login_required
@require_GET
def download_gazette(request, gazetteId):
    gazette = get_object_or_404(Gazette, id=gazetteId)
    fs = FileSystemStorage()
    filename = gazette.file.path
    if fs.exists(filename):
        with fs.open(filename) as pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="{0}.pdf"'.format(gazette.name)
            return response
    else:
        return HttpResponseNotFound('The requested pdf was not found in our server.')

@login_required
@require_POST
def rotate_img(request, model, modelId, rotation):

    if model == 'post' :
        obj = get_object_or_404(Post, id=modelId)
        if request.user.profile == obj.user :
            path = obj.photo.path
        else :
            return HttpResponseForbidden("Action Forbidden.")
    elif model == 'profile':
        obj = get_object_or_404(Profile, id=request.user.id)
        path = obj.avatar.path
    else :
        return HttpResponseForbidden("Action Forbidden.")
    
    rotate = [Image.ROTATE_90, Image.ROTATE_180, Image.ROTATE_270]
    
    image = Image.open(path)
    image = image.transpose(rotate[rotation-1])
    image.save(path)

    if model == 'profile':
        return redirect('updateProfile')
    else : 
        return redirect('update{0}'.format(model.capitalize()), modelId)
