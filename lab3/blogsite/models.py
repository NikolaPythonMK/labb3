from django.db import models
from django.contrib.auth.models import User


class AppUser(models.Model):
    username = models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date_joined = models.DateField(verbose_name="Date of account creation")

    @property
    def blocked_by(self):
        return AppUserBlock.objects.filter(blocked_user__username=self.username).values_list('blocking_user__id',
                                                                                             flat=True)

    def __str__(self):
        return self.username


class BlogPost(models.Model):
    posted_by = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=250)
    content = models.TextField(null=True, blank=True)
    date_created = models.DateField(verbose_name="Date Of Creation")
    last_modified = models.DateTimeField(verbose_name="Date Of Last Modification")

    def __str__(self):
        return self.title


class Upload(models.Model):
    blog_post = models.ForeignKey(BlogPost, on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploads/')


class AppUserBlock(models.Model):
    blocking_user = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='blocking_user')
    blocked_user = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='blocked_user')

    def __str__(self):
        return self.blocking_user.username + " blocked " + self.blocked_user.username


class Comment(models.Model):
    app_user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    blog_post = models.ForeignKey(BlogPost, on_delete=models.CASCADE)
    date_created = models.DateField()
    content = models.TextField()

