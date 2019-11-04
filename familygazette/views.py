from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.views.generic import ListView, DeleteView
from django.contrib.auth.decorators import login_required
from .models import Family, Post, Comment, Profile, Suggestion, Gazette, Conversation, Message
from .forms import LoginForm, UserForm, ProfileForm, PostForm, UpdatePostForm, CommentForm, SuggestionForm, MailForm, ConversationForm, MessageForm
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST, require_GET
from django.core.paginator import Paginator
from django.core import mail, serializers
from django.template.loader import render_to_string, get_template
from django.template import RequestContext
from django.utils.html import strip_tags
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseForbidden, HttpResponseServerError
from django.conf import settings
import xlwt, zipfile, os
from django.core.files.storage import FileSystemStorage
from PIL import Image
from django.db.models import Count
import json

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
def accessMedia(request):
    response = HttpResponse('')
    response['X-Accel-Redirect'] = request.path.replace('media', 'files')
    response['Content-Type'] = ''
    return response

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
    update = False
    posted =  False

    if request.method == 'POST':
        posted = True

    form = PostForm(request.POST or None, request.FILES or None, user=request.user.profile)
    
    if form.is_valid():
        families = form.cleaned_data['families']
        uploaded_photo = form.cleaned_data['photo']
        for family in families :
            selected_family = get_object_or_404(Family, id=family.id)
            new_post = Post()
            new_post.title = form.cleaned_data['title']
            new_post.event_date = form.cleaned_data['event_date']
            new_post.photo = uploaded_photo
            new_post.user = request.user.profile
            new_post.family = selected_family
            new_post.save()

            new_post.compressImage()

            for member in selected_family.members.all().exclude(user=request.user) :
                if member.postNewsletter and member.user.email :
                    subject = 'Nouveau post pour la famille ' + selected_family.name
                    content = 'Nouveau post : \'{0}\' par {1}'.format(new_post.title, request.user.username)
                    context = {
                        'subject': subject,
                        'content': content,
                        'url': 'family/' + str(selected_family.id),
                        'fromForm': False
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
            'error': error,
            'update': True
        })
    else :
        return HttpResponseForbidden("Action Forbidden.")

@login_required
@require_POST
def delete_post(request, postId):
    post = get_object_or_404(Post, id=postId)
    if request.user.profile == post.user :
        familyId = post.family.id
        post.photo.delete()
        post.delete()

        return redirect('family', familyId=familyId)
    else:
        return HttpResponseForbidden("Action Forbidden.")

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
        
        if selected_post.user.user != request.user and selected_post.user.commentNewsletter and selected_post.user.user.email :
            subject = 'Nouveau commentaire de ' + request.user.username
            content = 'Nouveau commentaire sur votre photo \'{0}\''.format(selected_post.title)
            context = {
                'subject': subject,
                'content': content,
                'url': 'family/' + str(selected_post.family.id),
                'fromForm': False
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
                if user.commentNewsletter and user.user.email :
                    subject = 'Nouveau commentaire de ' + request.user.username
                    content = '{0} a également commenté la photo \'{1}\''.format(request.user.username, selected_post.title)
                    context = {
                        'subject': subject,
                        'content': content,
                        'url': 'family/' + str(selected_post.family.id),
                        'fromForm': False
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
def update_comment(request, commentId):
    
    comment = get_object_or_404(Comment, id=commentId)
    if request.user.profile == comment.user :
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('family', familyId=comment.post.family.id)
        else:
            return redirect('family', familyId=comment.post.family.id)
    else:
        return HttpResponseForbidden("Action Forbidden.")

    
@login_required
@require_POST
def delete_comment(request, commentId):

    comment = get_object_or_404(Comment, id=commentId)
    if request.user.profile == comment.user :
        comment.delete()
        return redirect('family', familyId=comment.post.family.id)
    else:
        return HttpResponseForbidden("Action Forbidden.")

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
            'url': 'suggestions',
            'fromForm': False
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
    posts = Post.objects.filter(family__id=familyId).order_by('event_date')
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
    column = ['title', 'date', 'user', 'avatar', 'filename']
    files = []
    avatars = []
    #column.append('family')
    #row.append(family.name)
    for num,post in enumerate(posts):
        file_name = post.photo.path.split('/')[-1]
        if post.user.avatar:
            avatar_path = post.user.avatar.path.split('/')[-1]
        else:
            avatar_path = None
        rows.append([post.title, post.event_date.strftime("%d/%m/%y"), '{0} {1}'.format(post.user.user.first_name, post.user.user.last_name), avatar_path, file_name])
        files.append(file_name)
        if avatar_path and avatar_path not in avatars:
            avatars.append(avatar_path)

    for col_num in range(len(column)):
        ws.write(row_num, col_num, column[col_num], font_style) # at 0 row 0 column 

    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

    wb.save('media/familygazetteExcel.xls')

    response = HttpResponse(content_type='application/zip')
    zf = zipfile.ZipFile(response, 'w')
    zf.write('media/familygazetteExcel.xls')
    for filename in files:
        zf.write(os.path.join('media/photos', filename))
    for filename in avatars:
        zf.write(os.path.join('media/avatars', filename))

    response['Content-Disposition'] = 'attachment; filename=familygazette_{}.zip'.format(family.name)

    os.remove("media/familygazetteExcel.xls")
    
    return response

class ListGazettes(LoginRequiredMixin, ListView):
    model = Gazette
    context_object_name = "gazettes"
    template_name = "gazettes.html"
    #paginate_by = 5 # attribut de pagination

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

@login_required
def messages(request):

    conversations = Conversation.objects.filter(users=request.user.profile)
    users = Profile.objects.filter(family__in=request.user.profile.families).distinct().exclude(user=request.user)

    return render(request, 'messages.html', {
        'conversations': conversations,
        'users': users
    })

@login_required
@require_POST
def new_conversation(request):

    conversation_form = ConversationForm(request.POST, user=request.user.profile)
    message_form = MessageForm(request.POST)
    if conversation_form.is_valid() and message_form.is_valid():
        conversation_users = conversation_form.cleaned_data['users']
        query = Conversation.objects.annotate(count=Count('users')).filter(count=(len(conversation_users)+1)).filter(users__id=request.user.profile.id)
        for user in conversation_users :
            query = query.filter(users__id=user.id)
        if not query.exists() :
            conversation = Conversation.objects.create()
            for conversation_user in conversation_users :
                conversation.users.add(conversation_user)
            conversation.users.add(request.user.profile)
            for user in conversation_users :
                if user.commentNewsletter and user.user.email :
                    subject = 'Nouveau message'
                    content = '{0} vous a envoyé un nouveau message !'.format(request.user.username)
                    context = {
                        'subject': subject,
                        'content': content,
                        'url': 'messages',
                        'fromForm': False
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

        else :
            conversation = query[0]
        message = Message()
        message.content = message_form.cleaned_data['content']
        message.sender = request.user.profile
        message.conversation = conversation
        message.save()
        message.seenBy.add(request.user.profile)
        Conversation.objects.filter(id=conversation.id).update(last_message=message.date)

        return redirect('messages')
    else:
        return redirect('messages')

@staff_member_required
@require_POST
def new_mail(request):

    form = MailForm(request.POST)
    if form.is_valid():
        subject = form.cleaned_data['subject']
        content = form.cleaned_data['content'].split('\n')
        context = {
            'subject': subject,
            'content': content,
            'url': 'home',
            'fromForm': True
        }
        html_message = render_to_string('mail.html', context)
        plain_message = strip_tags(html_message)
        for family in Family.objects.all() :
            for member in family.members.all().exclude(user=request.user) :
                    if member.generalNewsletter and member.user.email :
                        mail.send_mail(
                            subject,
                            plain_message,
                            settings.EMAIL_HOST_USER,
                            [member.user.email],
                            html_message=html_message
                        )
        return redirect('messages')
    else:
        return redirect('messages')

@login_required
@require_GET
def get_messages(request, conversationId):

    conversation = get_object_or_404(Conversation, id=conversationId)
    if request.user.profile in conversation.users.all() :
        pre_messages = conversation.messages
        messages = serializers.serialize('json', pre_messages)
        users = {}
        for user in conversation.users.all():
            users[user.id] = user.user.username
        data = {}
        data['messages'] = messages
        data['users'] = users
        for message in pre_messages :
            message.seenBy.add(request.user.profile)
        return HttpResponse(json.dumps(data), content_type='application/json')
    else:
        return HttpResponseForbidden("Action Forbidden.")

@login_required
@require_POST
def new_message(request, conversationId):

    conversation = get_object_or_404(Conversation, id=conversationId)
    if request.user.profile in conversation.users.all() :
        message_form = MessageForm(request.POST)
        if message_form.is_valid():
            message = Message()
            message.content = message_form.cleaned_data['content']
            message.sender = request.user.profile
            message.conversation = conversation
            message.save()
            message.seenBy.add(request.user.profile)
            Conversation.objects.filter(id=conversationId).update(last_message=message.date)
            pre_messages = Conversation.objects.get(id=conversationId).messages
            messages = serializers.serialize('json', pre_messages)
            users = {}
            for user in conversation.users.all():
                users[user.id] = user.user.username
            data = {}
            data['messages'] = messages
            data['users'] = users

            return HttpResponse(json.dumps(data), content_type='application/json')
        else:
            return HttpResponseServerError('Form not valid')
    else:
        return HttpResponseForbidden("Action Forbidden.")