from django.http import JsonResponse
from django.shortcuts import redirect, render
from users.forms.add_librarian_form import AddLibrarianForm
from ..base_view import is_librarian
from django.contrib.auth.decorators import user_passes_test
from ...service.service_instances import _librarian_service, _patron_service
from django.contrib import messages


@user_passes_test(is_librarian, login_url='gear:home')
def add_librarian(request):
    if request.method == 'POST':
        action = request.POST.get('action', 'promote')
        if action == 'promote':
            form = AddLibrarianForm(request.POST, user=request.user)
            if form.is_valid():
                librarian_data = form.cleaned_data
                librarians = form.cleaned_data.get("new_librarians")
                librarian_data["new_librarians"] = librarians
                result = _librarian_service.promote_to_librarian(
                    librarian_data, request.user)

                if isinstance(result, Exception):
                    form.add_error(None, result)
                    messages.error(request, "Failed to promote librarians.")
                else:
                    messages.success(request, "Successfully promoted to librarian.")
                    return redirect('gear:home')
        elif action == 'demote':
            librarians_to_demote = request.POST.getlist('librarians_to_demote')
            if librarians_to_demote:
                result = _librarian_service.demote_librarian(
                    {"librarians_to_demote": _librarian_service.get_all_librarians().filter(id__in=librarians_to_demote)},
                    request.user
                )
                if isinstance(result, Exception):
                    messages.error(request, "Failed to demote librarians.")
                else:
                    messages.success(request, "Successfully demoted to patron.")
                    return redirect('gear:home')
            else:
                messages.error(request, "Please select librarians to demote.")
    else:
        form = AddLibrarianForm(user=request.user)

    context = {
        'form': form,
        'librarians': _librarian_service.get_all_librarians().exclude(email=request.user.email)
    }

    return render(request, 'librarian/add_librarian.html', context)
