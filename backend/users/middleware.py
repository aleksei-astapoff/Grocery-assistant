from django.contrib.auth import get_user_model
from django.http import JsonResponse

from rest_framework.authtoken.models import Token

User = get_user_model()


class BlockUserMiddleware:
    """Проверка на блокировку Пользователей Администратором."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if 'Authorization' in request.headers:
            try:
                token_key = request.headers['Authorization'].split(' ')[-1]
                token = Token.objects.get(key=token_key)
                user = token.user
                if user.is_blocked:
                    return JsonResponse(
                        {'detail': 'Пользователь заблокирован!'},
                        status=401
                    )
            except Token.DoesNotExist:
                pass

        response = self.get_response(request)
        return response
