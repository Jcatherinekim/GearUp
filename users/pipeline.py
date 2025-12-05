from .models import UserProfile


def save_user_profile(backend, user, response, *args, **kwargs):

    if backend.name != 'google-oauth2':
        return

    name = response.get('name')
    email = response.get('email')
    #profile_picture = response.get('picture')

    profile, created = UserProfile.objects.get_or_create(user=user)
    profile.name = name or ""
    profile.email = email or ""
    #if profile_picture:
    #   profile.profile_picture = profile_picture
    profile.save()
