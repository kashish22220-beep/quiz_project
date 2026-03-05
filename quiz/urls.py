from django.urls import path
from . import views

app_name = 'quiz'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('quizzes/', views.quiz_list, name='quiz_list'),
    path('quizzes/<int:pk>/', views.quiz_detail, name='quiz_detail'),
    path('quizzes/<int:pk>/take/', views.take_quiz, name='take_quiz'),
    path('quizzes/<int:quiz_id>/add-questions/', views.add_questions_bulk, name='add_questions_bulk'),
    path('result/<int:attempt_id>/', views.result, name='result'),
    path('profile/', views.profile, name='profile'),
]