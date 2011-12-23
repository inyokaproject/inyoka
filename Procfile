web: ./extra/autoreload --log-level=DEBUG -b $(python -c 'from django.conf import settings; print settings.BASE_DOMAIN_NAME')
worker: python manage.py celeryd -l INFO -B
