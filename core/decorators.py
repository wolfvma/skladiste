from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """Decorator that requires the user to be an ADMIN."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_admin:
            messages.error(request, 'Nemate dozvolu za pristup toj stranici.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
