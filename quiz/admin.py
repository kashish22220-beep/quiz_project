from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin

from .models import Quiz, Question, Choice, Attempt, Profile
try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'published', 'created_at')
    list_filter = ('published',)
    search_fields = ('title',)


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3 
    min_num = 0
    verbose_name = "Choice"
    verbose_name_plural = "Choices"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'order')
    list_filter = ('quiz',)
    search_fields = ('text',)
    inlines = [ChoiceInline]

    def short_text(self, obj):
        return (obj.text[:60] + '...') if len(obj.text) > 60 else obj.text
    short_text.short_description = 'Question'


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct')
    list_filter = ('is_correct',)


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'score', 'completed_at')
    list_filter = ('quiz', 'completed_at')

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'profile'
    fk_name = 'user'


class CustomUserAdmin(DefaultUserAdmin):
    inlines = (ProfileInline,)


    list_display = ('username', 'first_name', 'last_name', 'email', 'get_roll_no', 'is_staff', 'is_active')

   
    list_filter = DefaultUserAdmin.list_filter
    search_fields = DefaultUserAdmin.search_fields
    ordering = DefaultUserAdmin.ordering
    filter_horizontal = DefaultUserAdmin.filter_horizontal

    def get_roll_no(self, obj):
        try:
            return obj.profile.roll_no
        except Profile.DoesNotExist:
            return ''
    get_roll_no.short_description = 'Roll No'
    get_roll_no.admin_order_field = 'profile__roll_no' 

   
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)

try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

admin.site.register(User, CustomUserAdmin)
