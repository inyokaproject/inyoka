web: python manage.py run_gunicorn --log-level=DEBUG -b $(python -c 'from django.conf import settings; print settings.BASE_DOMAIN_NAME') -w 10 -k egg:gunicorn#gevent
worker: python manage.py celeryd -l INFO
