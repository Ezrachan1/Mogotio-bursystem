from django.conf import settings


def constituency_info(request):
    """Add constituency information to context"""
    return {
        'CONSTITUENCY_NAME': settings.CONSTITUENCY_NAME,
        'CONSTITUENCY_CODE': settings.CONSTITUENCY_CODE,
        'CONSTITUENCY_EMAIL': settings.CONSTITUENCY_EMAIL,
        'CONSTITUENCY_PHONE': settings.CONSTITUENCY_PHONE,
        'DEBUG': settings.DEBUG,
    }