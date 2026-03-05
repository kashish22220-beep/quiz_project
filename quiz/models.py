from django.db import models, transaction
from django.conf import settings
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db.models import F, Max

class Quiz(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    published = models.BooleanField(default=False)
    time_limit_minutes = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Question(models.Model):
    QUESTION_TYPES = [
        ('single', 'Single choice'),
        ('multi', 'Multiple choice'),
        ('text', 'Text answer'),
    ]
    DIFFICULTY = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES, default='single')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY, default='medium')
    marks = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Q{self.id} [{self.quiz.title}]"

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=1024)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

class Attempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    score = models.FloatField(default=0.0)
    total = models.PositiveIntegerField(default=0)
    correct = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    responses = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Attempt {self.id} by {self.user}"

class AttemptAnswer(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(Choice, on_delete=models.SET_NULL, null=True, blank=True)
    selected_text = models.TextField(blank=True)
    is_correct = models.BooleanField(default=False)
    points_awarded = models.FloatField(default=0.0)
    answered_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"Answer {self.id} for Attempt {self.attempt_id}"

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    roll_no = models.CharField(max_length=50, unique=True, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} profile"

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        Profile.objects.get_or_create(user=instance)

@receiver(pre_save, sender=Question)
def adjust_orders_on_save(sender, instance, **kwargs):
    if not hasattr(instance, 'quiz') or instance.quiz is None:
        return
    quiz = instance.quiz
    with transaction.atomic():
        if instance.pk is None:
            if instance.order and instance.order > 0:
                sender.objects.filter(quiz=quiz, order__gte=instance.order).update(order=F('order') + 1)
            else:
                max_order = sender.objects.filter(quiz=quiz).aggregate(Max('order'))['order__max'] or 0
                instance.order = max_order + 1
        else:
            try:
                old = sender.objects.get(pk=instance.pk)
            except sender.DoesNotExist:
                return
            old_order = old.order or 0
            new_order = instance.order or 0
            if new_order == old_order:
                return
            if new_order < old_order:
                sender.objects.filter(quiz=quiz, order__gte=new_order, order__lt=old_order).exclude(pk=instance.pk).update(order=F('order') + 1)
            else:
                sender.objects.filter(quiz=quiz, order__gt=old_order, order__lte=new_order).exclude(pk=instance.pk).update(order=F('order') - 1)

@receiver(post_delete, sender=Question)
def reorder_questions_on_delete(sender, instance, **kwargs):
    quiz = instance.quiz
    deleted_order = instance.order or 0
    sender.objects.filter(quiz=quiz, order__gt=deleted_order).update(order=F('order') - 1)