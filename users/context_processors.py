from .service.service_instances import _librarian_service, _patron_service


def librarian_status(request):
    status = (
        _librarian_service.is_librarian(request.user)
        if request.user.is_authenticated
        else False
    )
    return {"is_librarian": status}


def patron_status(request):
    status = (
        _patron_service.is_patron(request.user)
        if request.user.is_authenticated
        else False
    )
    return {"is_patron": status}


def patron_notifications(request):
    if request.user.is_authenticated and _patron_service.is_patron(request.user):
        return {
            "notification_count": _patron_service.get_unread_request_notifications(
                request.user
            )
        }
    return {}
