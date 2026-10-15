from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

User = get_user_model()
user = User.objects.filter(is_active=True).first()

if user is None:
    print("No active user found")
else:
    refresh = RefreshToken.for_user(user)
    token_string = str(refresh)

    refresh.blacklist()
    print("Refresh token blacklisted: True")

    try:
        RefreshToken(token_string)
        print("Blacklisted token rejected: False")
    except TokenError:
        print("Blacklisted token rejected: True")