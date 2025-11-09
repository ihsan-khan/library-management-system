from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
from jinja2 import Environment


def url_for(name, *args, **kwargs):
    """URL generation function for Jinja2 templates"""
    return reverse(name, args=args, kwargs=kwargs)


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'static': staticfiles_storage.url,
        'url': reverse,
        'url_for': url_for,
    })
    return env