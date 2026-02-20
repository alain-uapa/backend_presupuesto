import logging
import traceback

logger = logging.getLogger(__name__)


def log_error(request, exception, extra_info=None):
    exc_traceback = traceback.format_exc()
    
    user_info = None
    if request.user.is_authenticated:
        user_info = {
            'username': request.user.username,
            'email': request.user.email,
        }
    
    extra = {
        'request_method': request.method,
        'request_path': request.path,
        'user': user_info,
    }
    
    if extra_info:
        extra.update(extra_info)
    
    logger.error(
        f"Exception: {str(exception)}\nTraceback: {exc_traceback}",
        extra=extra
    )


def error_json_response(exception, message="Error interno del servidor", status=500, extra_info=None):
    from django.http import JsonResponse
    
    error_data = {
        'error': message,
        'detail': str(exception),
    }
    
    if extra_info:
        error_data['extra'] = extra_info
    
    return JsonResponse(error_data, status=status)
