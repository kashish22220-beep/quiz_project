
# Quiz Project

Quick start:
1. Create a virtualenv and install requirements:
   ```
   python -m venv .venv
   .venv\Scripts\activate   
   pip install -r requirements.txt
   ```
2. Run migrations:
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```
3. Create a superuser:
   ```
   python manage.py createsuperuser
   ```
4. Run server:
   ```
   python manage.py runserver
   ```
5. Open http://127.0.0.1:8000/

Project layout:
- `quiz_project/` — Django project package (settings, urls, wsgi)
- `quiz/` — Django app (models, views, templates)
- Templates are placed under `quiz/templates/` so APP_DIRS=True will find them.
