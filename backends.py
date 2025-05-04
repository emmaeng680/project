from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Authentication backend that allows login with either username or email
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try to find a user matching the username provided
            user = User.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user
            User().set_password(password)
        return None