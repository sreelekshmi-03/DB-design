from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User
from .serializers import SignupSerializer, CustomTokenObtainPairSerializer


class SignupView(generics.CreateAPIView):
    """
    POST /api/auth/signup/
    body: {"username", "email", "phone", "role", "password"}
    Open to anyone - that's why permission_classes is overridden to AllowAny,
    since the project-wide default (see REST_FRAMEWORK settings) requires
    authentication otherwise.
    """
    queryset = User.objects.all()
    serializer_class = SignupSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login/
    body: {"email", "password"}
    Returns {"access": "...", "refresh": "..."} on success.
    SimpleJWT handles password checking and token creation; the custom
    serializer just adds role/email into the token payload.
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    body: {"refresh": "..."}
    Blacklists the refresh token so it can never be used again, even though
    JWTs are normally stateless. This requires the token_blacklist app
    (already added to INSTALLED_APPS) and its migrations applied.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({"detail": "Invalid or already blacklisted token."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "Logged out successfully."}, status=status.HTTP_205_RESET_CONTENT)


class MeView(APIView):
    """
    GET /api/auth/me/
    A protected sample endpoint: requires a valid access token in the
    Authorization header (Bearer <access_token>). Proves JWT protection works.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "role": user.role,
            "is_verified": user.is_verified,
        })