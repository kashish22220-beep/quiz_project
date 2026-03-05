import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quiz_project.settings')

import django
django.setup()

from django.core.mail import send_mail

print("EMAIL_BACKEND:", os.environ.get('EMAIL_BACKEND'))
print("EMAIL_HOST:", os.environ.get('EMAIL_HOST'))
print("EMAIL_HOST_USER:", os.environ.get('EMAIL_HOST_USER'))
print("PASSWORD_SET?", bool(os.environ.get('EMAIL_HOST_PASSWORD')))
print("PASSWORD_LEN:", len(os.environ.get('EMAIL_HOST_PASSWORD') or ""))
try:
    res = send_mail(
        'SMTP test',
        'Body from Django',
        os.environ.get('DEFAULT_FROM_EMAIL') or os.environ.get('EMAIL_HOST_USER'),
        ['kashshaikh66@gmail.com']   
    )
    print("send_mail returned:", res)
except Exception:
    import traceback; traceback.print_exc()