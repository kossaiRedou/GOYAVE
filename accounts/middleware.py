from django.utils.deprecation import MiddlewareMixin
from .models import UserAction
from django.contrib.contenttypes.models import ContentType

class UserActionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Ne pas logger les requêtes statiques ou admin
        if any(path in request.path for path in ['/static/', '/media/', '/admin/static/']):
            return None

        if request.user.is_authenticated:
            # Informations de base
            extra_data = {
                'ip': request.META.get('REMOTE_ADDR'),
                'user_agent': request.META.get('HTTP_USER_AGENT'),
                'path': request.path,
                'method': request.method,
            }

            # Déterminer le type d'action
            if request.method == 'GET':
                action_type = 'VIEW'
            elif request.method == 'POST':
                action_type = 'CREATE' if 'add' in request.path else 'UPDATE'
            elif request.method == 'DELETE':
                action_type = 'DELETE'
            else:
                action_type = 'VIEW'

            # Créer l'action
            UserAction.objects.create(
                user=request.user,
                action_type=action_type,
                description=f"{request.method} {request.path}",
                extra_data=extra_data
            ) 