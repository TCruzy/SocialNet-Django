from email.policy import default
import django
from django.db import models
from django.utils import timezone

# tbilisi_tz = timezone.now()
# print(tbilisi_tz)


class User(models.Model):
    username = models.CharField(max_length=20)
    password = models.CharField(max_length=20)
    profile_pic = models.ImageField(upload_to='static/pfp/', default='static/pfp/default.png')
    profile_info = models.CharField(max_length=20, default='Public')   


class Posts(models.Model):
    userId = models.ForeignKey(User, on_delete=models.CASCADE)
    poster_type = models.CharField(max_length=20,default='user')
    post_content = models.CharField(max_length=200)
    post_date = models.DateTimeField(auto_now_add=django.utils.timezone.now)
    image = models.ImageField(upload_to='static/img/', blank=True, null=True)
    
class Likes(models.Model):
    userId = models.ForeignKey(User, on_delete=models.CASCADE)
    postId = models.ForeignKey(Posts, on_delete=models.CASCADE)
    like_date = models.DateTimeField(auto_now_add=django.utils.timezone.now)

class Followers(models.Model):
    userId = models.IntegerField()
    followerId = models.IntegerField()
    follow_date = models.DateTimeField(auto_now_add=django.utils.timezone.now)