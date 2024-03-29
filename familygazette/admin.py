from django.contrib import admin
from .models import Family, Post, Comment, Profile, Suggestion, Gazette, Message

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'birthday', 'generalNewsletter', 'postNewsletter', 'commentNewsletter')
    ordering = ('user',)
    list_filter = ('generalNewsletter', 'postNewsletter', 'commentNewsletter')

class FamilyAdmin(admin.ModelAdmin):
    list_display = ('name', 'creation_date')
    ordering = ('name',)
    search_fields = ('name',)

class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'publication_date', 'event_date')
    list_filter = ('user', 'family')
    date_hierarchy = 'publication_date'
    ordering = ('publication_date', 'event_date')
    search_fields = ('title', 'user', 'event_date')

class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'date', 'user')
    list_filter = ('post', 'user')
    ordering = ('date',)
    search_fields = ('post', 'date', 'user')

class SuggestionAdmin(admin.ModelAdmin):
    list_display = ('date', 'user')
    ordering = ('date',)

class GazetteAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'family')
    list_filter = ('family',)
    ordering = ('-date',)

class MessageAdmin(admin.ModelAdmin):
    list_display = ('date', 'sender', 'conversation')
    list_filter = ('sender', 'conversation')
    ordering = ('-date',)
    search_fields = ('sender', 'conversation')

admin.site.register(Profile, ProfileAdmin)
admin.site.register(Family, FamilyAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Suggestion, SuggestionAdmin)
admin.site.register(Gazette, GazetteAdmin)
admin.site.register(Message, MessageAdmin)