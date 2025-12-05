from django.shortcuts import redirect
from ..service.service_instances import _librarian_service, _patron_service
from django.contrib.auth import logout


def logout_view(request):
    logout(request)
    return redirect("gear:home")


def is_librarian(user):
    return _librarian_service.is_librarian(user)


def is_patron(user):
    return _patron_service.is_patron(user)
