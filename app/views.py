"""
Authentication + Profile CRUD views.
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import NotFound

from .models import Candidate, Employer, User
from .profile_permissions import IsSelfOrAdmin
from .profile_serializers import (
    CandidateProfileSerializer,
    EmployerProfileSerializer,
)


# =========================================================
# Authentication
# =========================================================

class SignupView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        role = request.data.get("role")

        if not email or not password or not role:
            return Response(
                {"detail": "email, password and role are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = email.strip().lower()

        if User.objects.filter(email=email).exists():
            return Response(
                {"detail": "A user with this email already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid_roles = [
            User.Role.CANDIDATE,
            User.Role.EMPLOYER,
        ]

        if role not in valid_roles:
            return Response(
                {"detail": "Invalid role. Choose candidate or employer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(password) < 8:
            return Response(
                {"detail": "Password must be at least 8 characters long."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            email=email,
            password=password,
            role=role,
        )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role,
                },
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"detail": "email and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = email.strip().lower()

        user = User.objects.filter(email=email).first()

        if user is None or not user.check_password(password):
            return Response(
                {"detail": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"detail": "This account is inactive."},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role,
                },
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"detail": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"detail": "Successfully logged out."},
                status=status.HTTP_205_RESET_CONTENT,
            )

        except Exception:
            return Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        return Response(
            {
                "id": user.id,
                "email": user.email,
                "role": user.role,
            },
            status=status.HTTP_200_OK,
        )


# =========================================================
# Candidate Profile
# =========================================================

class MyCandidateProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = CandidateProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        try:
            obj = self.request.user.candidate_profile
        except Candidate.DoesNotExist:
            raise NotFound("Candidate profile not found.")

        self.check_object_permissions(self.request, obj)
        return obj


class CandidateProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CandidateProfileSerializer
    queryset = Candidate.objects.all()
    permission_classes = [
        permissions.IsAuthenticated,
        IsSelfOrAdmin,
    ]

    def perform_destroy(self, instance):
        instance.soft_delete()


# =========================================================
# Employer Profile
# =========================================================

class MyEmployerProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = EmployerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        try:
            obj = self.request.user.employer_profile
        except Employer.DoesNotExist:
            raise NotFound("Employer profile not found.")

        self.check_object_permissions(self.request, obj)
        return obj


class EmployerProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EmployerProfileSerializer
    queryset = Employer.objects.all()
    permission_classes = [
        permissions.IsAuthenticated,
        IsSelfOrAdmin,
    ]

    def perform_destroy(self, instance):
        instance.soft_delete()


# =========================================================
# Admin Operations
# =========================================================

class AdminEmployerVerifyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != User.Role.ADMIN:
            return Response(
                {"detail": "Only admins can verify a company."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            employer = Employer.all_objects.get(pk=pk)
        except Employer.DoesNotExist:
            return Response(
                {"detail": "Employer not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        employer.is_company_verified = True
        employer.save(update_fields=["is_company_verified"])

        return Response(
            {"detail": f"{employer.company_name} verified."},
            status=status.HTTP_200_OK,
        )


class AdminRestoreProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, kind, pk):
        if request.user.role != User.Role.ADMIN:
            return Response(
                {"detail": "Only admins can restore a profile."},
                status=status.HTTP_403_FORBIDDEN,
            )

        model = {
            "candidate": Candidate,
            "employer": Employer,
        }.get(kind)

        if model is None:
            return Response(
                {
                    "detail": (
                        "kind must be 'candidate' or 'employer'."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            obj = model.all_objects.get(pk=pk)
        except model.DoesNotExist:
            return Response(
                {"detail": "Profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        obj.restore()

        return Response(
            {"detail": "Profile restored."},
            status=status.HTTP_200_OK,
        )