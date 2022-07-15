from main.settings import BASE_DIR


SECRET_KEY = 'django-insecure-)&@04r9ti6aw9ji^pbsnv0jf1vt=3qpmu!6mw$k5!xoe^s*#c0'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

DEBUG = True