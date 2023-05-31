import re

from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import ngettext
from rangefilter.filter import DateRangeFilter

from .models import BlogPost, Upload, AppUser, AppUserBlock, Comment

staff_group, created = Group.objects.get_or_create(name='staff')


@admin.action(description="Block selected users")
def block_users(modeladmin, request, queryset):
    current_app_user = get_object_or_404(AppUser, username=request.user.username)
    if current_app_user in queryset:
        modeladmin.message_user(request, "You can't select yourself to be included in your blocklist.", messages.ERROR)
        return
    successfully_blocked = 0
    for app_user in queryset:
        # prevent a user from blocking the same user multiple times
        if not AppUserBlock.objects.filter(blocking_user=current_app_user, blocked_user=app_user).exists():
            AppUserBlock.objects.create(blocking_user=current_app_user, blocked_user=app_user)
            successfully_blocked += 1
    modeladmin.message_user(request,
                            ngettext('%d user successfully blocked.',
                                     '%d users successfully blocked.',
                                     successfully_blocked) % successfully_blocked, messages.SUCCESS)


@admin.action(description="Unblock selected users")
def unblock_users(modeladmin, request, queryset):
    current_app_user = get_object_or_404(AppUser, username=request.user.username)
    unblocked_users = AppUserBlock.objects.filter(blocking_user=current_app_user, blocked_user__in=queryset).delete()
    modeladmin.message_user(request,
                            ngettext('%d user successfully unblocked.',
                                     '%d users successfully unblocked.',
                                     unblocked_users[0]) % unblocked_users[0], messages.SUCCESS)


@admin.register(AppUser)
class AppUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'date_joined')
    exclude = ('username', 'date_joined')
    actions = (block_users, unblock_users)

    def save_model(self, request, obj, form, change):
        if request.path.endswith('add/'):
            user = get_object_or_404(User, pk=request.POST['user'])
            user.groups.add(staff_group)
            obj.username = user.username
            obj.date_joined = user.date_joined
            super().save_model(request, obj, form, change)
        elif request.path.endswith('change/'):
            user = request.user
            new_first_name = request.POST['first_name']
            new_last_name = request.POST['last_name']
            user.first_name = new_first_name
            user.last_name = new_last_name
            user.save()
            super().save_model(request, obj, form, change)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        self.exclude = ('user', 'username', 'date_joined')
        return super().change_view(request, object_id, form_url, extra_context)

    def add_view(self, request, form_url="", extra_context=None):
        self.exclude = ('username', 'date_joined')
        return super().add_view(request, form_url, extra_context)

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        matches = re.findall('\d+', request.path)
        if len(matches) == 0:
            return True
        if '/admin/blogsite/appuser' in request.path:
            user_id = int(matches[0])
            user_from_db = get_object_or_404(AppUser, pk=user_id)
            return request.user.username == user_from_db.username
        return True

    def has_view_permission(self, request, obj=None):
        return True


class UploadAdmin(admin.StackedInline):
    model = Upload
    extra = 0


class CommentAdmin(admin.StackedInline):
    model = Comment
    extra = 0
    exclude = ('app_user', 'date_created')

    # def has_change_permission(self, request, obj=None):
    #     current_app_user = get_object_or_404(AppUser, username=request.user.username)
    #     if request.method == 'POST':
    #         comment_id = int(request.POST['comment_set-0-id'])
    #         comment = get_object_or_404(Comment, pk=comment_id)
    #         return current_app_user == comment.app_user or current_app_user == obj.posted_by
    #     else:
    #         return True

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)

    def has_add_permission(self, request, obj):
        return True


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'posted_by')
    list_filter = (('date_created', DateRangeFilter),)
    exclude = ('posted_by', 'date_created', 'last_modified')
    inlines = (UploadAdmin, CommentAdmin)
    search_fields = ('title', 'content')

    def save_model(self, request, obj, form, change):
        app_user = get_object_or_404(AppUser, username=request.user.username)
        obj.posted_by = app_user
        obj.date_created = obj.date_created if obj.date_created else timezone.now()
        obj.last_modified = timezone.now()
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        app_user = get_object_or_404(AppUser, username=request.user.username)
        instances = formset.save(commit=False)
        for instance in instances:
            instance.app_user = app_user
            instance.date_created = timezone.now()
            instance.save()
        formset.save_m2m()

    def has_view_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return True
        current_user = get_object_or_404(AppUser, username=request.user.username)
        return current_user.id == obj.posted_by.id

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return self.has_change_permission(request, obj)

    def get_queryset(self, request):
        current_app_user = get_object_or_404(AppUser, username=request.user.username)
        return BlogPost.objects.exclude(
            id__in=BlogPost.objects.filter(
                posted_by_id__in=current_app_user.blocked_by
            )
        )

