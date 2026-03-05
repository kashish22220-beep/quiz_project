import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quiz_project.settings')

import django
django.setup()

from django.contrib.auth.forms import PasswordResetForm
import os as _os

EMAIL = 'recipient@example.com' 

print("ENV EMAIL_BACKEND:", _os.environ.get('EMAIL_BACKEND'))
print("ENV EMAIL_HOST_USER:", _os.environ.get('EMAIL_HOST_USER'))
print("PASSWORD_SET?", bool(_os.environ.get('EMAIL_HOST_PASSWORD')))
print("DEFAULT_FROM_EMAIL:", _os.environ.get('DEFAULT_FROM_EMAIL'))

f = PasswordResetForm({'email': EMAIL})
print("form.is_valid():", f.is_valid())
if f.is_valid():
    try:
        f.save(domain_override='127.0.0.1:8000', use_https=False)
        print("PasswordResetForm.save() finished without exception")
    except Exception:
        import traceback
        traceback.print_exc()
else:
    print("No user found for that email")