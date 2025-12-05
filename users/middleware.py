from django.shortcuts import redirect


class AdminRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.is_superuser:
            if not request.path.startswith("/admin/"):
                return redirect("/admin/")
        return self.get_response(request)
