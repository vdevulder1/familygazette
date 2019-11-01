"""familygazette URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, reverse_lazy, re_path
from django.contrib.auth import views as auth_views
from . import views
from django.conf.urls.static import static
from django.conf import settings
from django.conf.urls import (
handler400, handler403, handler404, handler500
)

handler400 = 'familygazette.views.handler400'
handler403 = 'familygazette.views.handler403'
handler404 = 'familygazette.views.handler404'
handler500 = 'familygazette.views.handler500'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login', views.logIn, name="login"),
    path('logout', views.logOut, name="logout"),
    #re_path(r'^media', views.accessMedia),
    path('password/change/', auth_views.PasswordChangeView.as_view(), name="password_change"),
    path('password/change/done/', auth_views.PasswordChangeDoneView.as_view(), name="password_change_done"),
    path('password/reset/', auth_views.PasswordResetView.as_view(), name="password_reset"),
    path('password/reset/done/', auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path('password/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path('password/reset/complete/', auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
    path('', views.home),
    path('home', views.home, name="home"),
    path('family/<int:familyId>', views.ListPosts.as_view(), name='family'),
    path('profile/update', views.update_profile, name="updateProfile"),
    path('profile/<int:profileId>', views.get_profile, name="getProfile"),
    path('profile/me', views.my_profile, name="myProfile"),
    path('post/<int:familyId>/new-post', views.create_post, name="newPost"),
    path('post/<int:postId>/update', views.update_post, name="updatePost"),
    path('post/<int:postId>/delete', views.delete_post, name="deletePost"),
    path('post/<int:familyId>/<int:postId>/new-comment', views.create_comment, name="newComment"),
    path('comment/<int:commentId>/update', views.update_comment, name="updateComment"),
    path('comment/<int:commentId>/delete', views.delete_comment, name="deleteComment"),
    path('suggestions', views.ListSuggestions.as_view(), name='suggestions'),
    path('suggestions/new-suggestion', views.create_suggestion, name="newSuggestion"),
    path('suggestions/<int:suggestionId>/like', views.like_suggestion, name="likeSuggestion"),
    path('family/<int:familyId>/generate-document', views.generate_gazette, name="generateDocument"),
    path('family/<int:familyId>/gazettes', views.ListGazettes.as_view(), name='gazettes'),
    path('family/download/<int:gazetteId>', views.download_gazette, name='downloadGazette'),
    path('family/<int:familyId>/members', views.ListMembers.as_view(), name='members'),
    path('<str:model>/<int:modelId>/rotate/<int:rotation>', views.rotate_img, name="rotate"),
    path('messages', views.messages, name='messages'),
    path('messages/new-mail', views.new_mail, name='newMail'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
