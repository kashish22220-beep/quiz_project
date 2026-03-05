from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.db import transaction
from django.conf import settings

import json
from django.db import models


from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage


from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy


from .models import Quiz, Question, Choice, Attempt, AttemptAnswer, Profile


from .forms import MyUserCreationForm


from django.contrib.auth import login as auth_login, get_user_model

User = get_user_model()


class CustomLoginView(LoginView):
   
    template_name = 'registration/login.html' 
    def get_success_url(self):
        user = self.request.user
       
        if user.is_staff or user.is_superuser:
            return reverse_lazy('quiz:admin_dashboard')
        return reverse_lazy('quiz:home') 

def home(request):
   
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('quiz:admin_dashboard')
        return redirect('quiz:user_dashboard')

    
    if request.method == 'POST':
        form = AuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            if user.is_staff or user.is_superuser:
                return redirect('quiz:admin_dashboard')
            return redirect('quiz:user_dashboard')
        else:
            return render(request, 'index.html', {'form': form})
    else:
        form = AuthenticationForm(request=request)
        return render(request, 'index.html', {'form': form})


def register(request):
    
    if request.user.is_authenticated and not (request.user.is_staff or request.user.is_superuser):
        return redirect('quiz:user_dashboard')

    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

           
            if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
                user.is_active = True
                user.save()
                if hasattr(form, "save_m2m"):
                    form.save_m2m()
                # profile
                roll_no = form.cleaned_data.get('roll_no', '')
                Profile.objects.get_or_create(user=user)
                if roll_no:
                    profile = user.profile
                    profile.roll_no = roll_no
                    profile.save()
                messages.success(request, f'User {user.username} created.')
                return redirect('quiz:admin_dashboard')

            user.is_active = True
            user.save()
            if hasattr(form, "save_m2m"):
                form.save_m2m()

            roll_no = form.cleaned_data.get('roll_no', '')
            Profile.objects.get_or_create(user=user)
            if roll_no:
                profile = user.profile
                profile.roll_no = roll_no
                profile.save()

           
            auth_login(request, user)
            messages.success(request, 'Registration successful. Welcome!')
            return redirect('quiz:user_dashboard')
    else:
        form = MyUserCreationForm()

    return render(request, 'registration/signup.html', {'form': form})


def activate(request, uidb64, token):
    """
    Activation link handler. If token valid, activate the user.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Your account has been activated. You can now log in.")
        return render(request, 'registration/account_activation_complete.html')
    else:
        return render(request, 'registration/account_activation_invalid.html')


@login_required
def user_dashboard(request):
    quizzes = Quiz.objects.filter(published=True).order_by('-created_at')
    return render(request, 'quiz/user_dashboard.html', {'quizzes': quizzes})


@staff_member_required
def admin_dashboard(request):
    quizzes = Quiz.objects.all().order_by('-created_at')
    return render(request, 'quiz/admin_dashboard.html', {'quizzes': quizzes})


def quiz_list(request):
    quizzes = Quiz.objects.filter(published=True).order_by('-created_at')
    return render(request, 'quiz/quiz_list.html', {'quizzes': quizzes})


def quiz_detail(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    questions = quiz.questions.all()
    return render(request, 'quiz/quiz_detail.html', {'quiz': quiz, 'questions': questions})


@login_required
def take_quiz(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    questions = quiz.questions.all().order_by('order', 'id')

    if request.method == 'POST':
        
        with transaction.atomic():
            attempt = Attempt.objects.create(user=request.user, quiz=quiz, started_at=timezone.now())
            total = questions.count()
            correct_count = 0
            responses = {}

            for question in questions:
                qname = f"question_{question.id}"
                selected = request.POST.getlist(qname)
                selected_ids = [int(x) for x in selected] if selected else []

                correct_choices = list(question.choices.filter(is_correct=True).values_list('id', flat=True))
                is_q_correct = set(correct_choices) == set(selected_ids)
                if is_q_correct:
                    correct_count += 1

                selected_choice = None
                if len(selected_ids) == 1:
                    selected_choice = Choice.objects.filter(id=selected_ids[0]).first()

                AttemptAnswer.objects.create(
                    attempt=attempt,
                    question=question,
                    selected_choice=selected_choice,
                    selected_text=','.join(str(i) for i in selected_ids) if selected_ids else '',
                    is_correct=is_q_correct,
                    points_awarded=1.0 if is_q_correct else 0.0
                )

                responses[str(question.id)] = selected_ids

            attempt.total = total
            attempt.correct = correct_count
            attempt.score = (correct_count / total * 100.0) if total else 0.0
            attempt.completed_at = timezone.now()
            attempt.responses = responses
            attempt.save()

        return redirect('quiz:result', attempt_id=attempt.id)

    return render(request, 'quiz/take_quiz.html', {'quiz': quiz, 'questions': questions})


@login_required
def result(request, attempt_id):
    """
    Result view — shows attempt details. Name matches URL used in templates.
    """
    attempt = get_object_or_404(Attempt, id=attempt_id)
    if attempt.user != request.user and not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden("You cannot view this result.")
    answers = attempt.answers.all()
    return render(request, 'quiz/result.html', {'attempt': attempt, 'answers': answers})


@login_required
def profile(request):
    attempts = Attempt.objects.filter(user=request.user).order_by('-completed_at')
    return render(request, 'quiz/profile.html', {'profile_user': request.user, 'attempts': attempts})


@staff_member_required
def add_questions_bulk(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)

    if request.method == 'GET':
        return render(request, 'quiz/add_questions_bulk.html', {'quiz': quiz})

    payload_raw = request.POST.get('payload') or request.body.decode('utf-8')
    if not payload_raw:
        return render(request, 'quiz/add_questions_bulk.html', {'quiz': quiz, 'error': 'No data submitted'})

    try:
        data = json.loads(payload_raw)
    except json.JSONDecodeError:
        return render(request, 'quiz/add_questions_bulk.html', {'quiz': quiz, 'error': 'Invalid JSON'})

    questions = data.get('questions', [])
    created_count = 0

    max_order = quiz.questions.aggregate(models.Max('order'))['order__max'] or 0
    next_order = max_order + 1

    for q in questions:
        text = q.get('text', '').strip()
        if not text:
            continue
        q_type = q.get('question_type', 'single')
        difficulty = q.get('difficulty', 'medium')
        marks = int(q.get('marks', 1))
        order = next_order
        next_order += 1

        question = Question.objects.create(
            quiz=quiz,
            text=text,
            order=order,
            question_type=q_type,
            difficulty=difficulty if hasattr(Question, 'difficulty') else 'medium',
            marks=marks
        )

        choices = q.get('choices', [])
        for c in choices:
            c_text = c.get('text', '').strip()
            if not c_text:
                continue
            is_corr = bool(c.get('is_correct', False))
            Choice.objects.create(question=question, text=c_text, is_correct=is_corr)

        created_count += 1

    messages.success(request, f'Created {created_count} questions for quiz \"{quiz.title}\".')
    return redirect('quiz:admin_dashboard')