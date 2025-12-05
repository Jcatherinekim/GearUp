from django.shortcuts import redirect, render
from gear.models import Collection
from users.forms.edit_profile_form import ProfilePictureForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages


@login_required
def profile(request):
    user_profile = request.user.userprofile
    collections = Collection.objects.filter(created_by=user_profile)

    context = {
        "user": request.user,
        "collections": collections,
    }
    return render(request, "profile.html", context)


@login_required
def update_user(request):
    if request.method == "POST":
        form = ProfilePictureForm(
            request.POST, request.FILES, instance=request.user.userprofile
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("users:profile")
    else:
        form = ProfilePictureForm(instance=request.user.userprofile)

    context = {
        "form": form,
    }

    return render(request, "update_profile.html", context)
