from django.conf import settings


def project_context():
    return {
        'project_name': settings.PROJECT_NAME
    }
