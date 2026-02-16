from django.http import JsonResponse
from functools import wraps

def login_required_json(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {'error': 'No autorizado. Por favor inicia sesión.'}, 
                status=401
            )
        return view_func(request, *args, **kwargs)
    return _wrapped_view