import os
from django.core.wsgi import get_wsgi_application # pyright: ignore[reportMissingModuleSource]

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'milkproject.settings')
application = get_wsgi_application()
