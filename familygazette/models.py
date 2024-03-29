import sys
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # La liaison OneToOne vers le modèle User
    birthday = models.DateField(auto_now=False, auto_now_add=False, null=True, blank=True, verbose_name="Date de naissance")
    avatar = models.ImageField(null=True, blank=True, upload_to="avatars/")
    generalNewsletter = models.BooleanField(default=True, verbose_name="Newsletter générale")
    postNewsletter = models.BooleanField(default=True, verbose_name="Suivi de post")
    commentNewsletter = models.BooleanField(default=True, verbose_name="Suivi de commentaire")

    def __str__(self):
        return self.user.username

    def compressAvatar(self):
        compress_Image(self, 'avatar', 960, 540)

    @property
    def families(self):
        """
        Permet de récupérer l'ensemble des familles auquel appartient le User
        """
        return self.family_set.all()

    def unseenMessages(self):
        unreadMessages = 0
        for conversation in Conversation.objects.filter(users__id=self.id):
            unreadMessages += conversation.unseen_messages_count(self)

        return unreadMessages
    
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Family(models.Model):
    name = models.CharField(max_length=40)
    description = models.TextField(max_length=100)
    creation_date = models.DateTimeField(default=timezone.now, verbose_name="Date de création")
    members = models.ManyToManyField(Profile)
    photo = models.ImageField(null=True, blank=True, upload_to="photos/")

    class Meta :
        ordering = ['name']

    def __str__(self):
        return self.name

    def unseen_elements_count(self, user):
        """
        Retourne le nombre d'éléments non lus par un user
        """
        return self.unseen_posts_count(user) + self.unseen_gazettes_count(user)

    def unseen_posts_count(self, user):
        """
        Retourne le nombre de posts non lus par un user
        """
        return self.post_set.exclude(seenBy__id=user.id).count()

    def unseen_gazettes_count(self, user):
        """
        Retourne le nombre de gazettes non lues par un user
        """
        return self.gazette_set.exclude(seenBy__id=user.id).count()

    def compressImage(self):
        compress_Image(self, 'photo', 1920, 1080)

class Post(models.Model):
    title = models.CharField(max_length=100)
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    publication_date = models.DateTimeField(default=timezone.now, verbose_name="Date de publication")
    event_date = models.DateField(default=date.today, verbose_name="Date de l'évènement")
    family = models.ForeignKey(Family, on_delete=models.CASCADE, verbose_name="Famille")
    photo = models.ImageField(upload_to="photos/")
    seenBy = models.ManyToManyField(Profile, related_name='post_seenBy')

    class Meta:
        ordering = ['-publication_date']

    def __str__(self):
        return self.title

    def compressImage(self):
        compress_Image(self, 'photo', 1920, 1080)

    @property
    def comments(self):
        """
        Permet de récupérer l'ensemble des commentaires d'un
        post
        """
        return self.comment_set.all()

@receiver(pre_delete, sender=Post)
def delete_post(sender, instance, **kwargs):
    instance.photo.delete()

class Comment(models.Model):
    date = models.DateTimeField(verbose_name="Date de publication", auto_now_add=True, auto_now=False)
    content = models.TextField(max_length=400)
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return "Comment of {0} on {1}".format(self.user.__str__(), self.post.__str__())

class Suggestion(models.Model):
    date = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    content = models.TextField(max_length=500)
    likes = models.ManyToManyField(Profile, related_name='likes')

class Gazette(models.Model):
    date = models.DateTimeField(default=timezone.now)
    family = models.ForeignKey(Family, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default="gazette_familyname_date")
    file = models.FileField(upload_to="gazettes/")
    seenBy = models.ManyToManyField(Profile, related_name='gazette_seenBy')

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return "Gazette of {0} from the {1}".format(self.family, self.date)

class Conversation(models.Model):
    users = models.ManyToManyField(Profile)
    last_message = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '-'.join(map(lambda x: x.__str__(), self.users.all()))
    
    class Meta:
        ordering = ['-last_message']

    @property
    def messages(self):
        """
        Permet de récupérer l'ensemble des messages d'une conversation
        """
        return self.message_set.all()

    def unseen_messages_count(self, user):
        """
        Retourne le nombre de messages non lus par un user
        """
        return self.message_set.exclude(seenBy__id=user.id).count()


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    date = models.DateTimeField(default=timezone.now)
    sender = models.ForeignKey(Profile, on_delete=models.CASCADE)
    seenBy = models.ManyToManyField(Profile, related_name='message_seenBy')
    content = models.TextField()

    def __str__(self):
        return "{0} - {1}".format(self.date, self.sender)

    class Meta:
        ordering = ['date']


def compress_Image(element, parameter, max_width, max_height):
        if parameter == 'photo' :
            obj = element.photo
        elif parameter == 'avatar' :
            obj = element.avatar
        else :
            return None

        imageTemproary = Image.open(obj.path)
        outputIoStream = BytesIO()

        width, height = imageTemproary.size
        if width == max(width, height) and width > max_width :
            ratio = height/width
            new_width = max_width
            new_height = int(ratio*new_width)
            imageTemproary = imageTemproary.resize((new_width, new_height), Image.ANTIALIAS)
        elif height == max(width, height) and height > max_height :
            ratio = width/height
            new_height = max_height
            new_width = int(ratio*new_height)
            imageTemproary = imageTemproary.resize((new_width, new_height), Image.ANTIALIAS)
        
        imageTemproary = imageTemproary.convert("RGB")
        imageTemproary.save(outputIoStream , format='JPEG', optimize=True, quality=70)
        outputIoStream.seek(0)
        name = obj.name.split('.')[0]
        obj.delete()
        if parameter == 'photo' :
            element.photo = InMemoryUploadedFile(outputIoStream,'ImageField', "%s.jpg" % name, 'image/jpeg', sys.getsizeof(outputIoStream), None)
        elif parameter == 'avatar' :
            element.avatar = InMemoryUploadedFile(outputIoStream,'ImageField', "%s.jpg" % name, 'image/jpeg', sys.getsizeof(outputIoStream), None)
        
        element.save()