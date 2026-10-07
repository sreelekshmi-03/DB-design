from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.urls import reverse

from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, Candidate, Employer
from .profile_permissions import IsSelfOrAdmin
from .profile_serializers import (
    CandidateProfileSerializer,
    EmployerProfileSerializer,
)
from .resume_validators import (
    validate_resume_file,
    compute_file_hash,
)


# ============================================================
# AUTHENTICATION
# ============================================================

class SignupView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        role = request.data.get("role")

        if not email or not password or not role:
            return Response(
                {
                    "detail": "email, password and role are required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = email.strip().lower()

        valid_roles = {
            User.Role.CANDIDATE,
            User.Role.EMPLOYER,
        }

        if role not in valid_roles:
            return Response(
                {
                    "detail": (
                        "Invalid role. "
                        "Use candidate or employer."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {"detail": "A user with this email already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            user = User.objects.create_user(
                email=email,
                password=password,
                role=role,
            )

            if role == User.Role.CANDIDATE:
                Candidate.objects.get_or_create(
                    user=user,
                    defaults={
                        "full_name": "",
                        "skills": [],
                        "education": [],
                        "experience_years": 0,
                    },
                )

            elif role == User.Role.EMPLOYER:
                Employer.objects.get_or_create(
                    user=user,
                    defaults={
                        "company_name": "",
                    },
                )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Signup successful.",
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
                {
                    "detail": "email and password are required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = email.strip().lower()

        user = authenticate(
            request=request,
            email=email,
            password=password,
        )

        if user is None:
            return Response(
                {"detail": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if getattr(user, "is_deleted", False):
            return Response(
                {"detail": "This account has been deleted."},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Login successful.",
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
                {"detail": "Logout successful."},
                status=status.HTTP_205_RESET_CONTENT,
            )

        except Exception:
            return Response(
                {"detail": "Invalid refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        data = {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "is_verified": getattr(
                user,
                "is_verified",
                False,
            ),
            "is_active": user.is_active,
        }

        return Response(data, status=status.HTTP_200_OK)


# ============================================================
# CANDIDATE PROFILE
# ============================================================

class MyCandidateProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = CandidateProfileSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get_object(self):
        return get_object_or_404(
            Candidate,
            user=self.request.user,
        )


class CandidateProfileDetailView(generics.RetrieveUpdateAPIView):
    queryset = Candidate.objects.all()
    serializer_class = CandidateProfileSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsSelfOrAdmin,
    ]


# ============================================================
# EMPLOYER PROFILE
# ============================================================

class MyEmployerProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = EmployerProfileSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get_object(self):
        return get_object_or_404(
            Employer,
            user=self.request.user,
        )


class EmployerProfileDetailView(generics.RetrieveUpdateAPIView):
    queryset = Employer.objects.all()
    serializer_class = EmployerProfileSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsSelfOrAdmin,
    ]


# ============================================================
# RESUME UPLOAD
# ============================================================

class ResumeUploadView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    parser_classes = [
        MultiPartParser,
        FormParser,
    ]

    def post(self, request):
        if request.user.role != User.Role.CANDIDATE:
            return Response(
                {
                    "detail": (
                        "Only candidates can upload resumes."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        candidate = get_object_or_404(
            Candidate,
            user=request.user,
        )

        resume = request.FILES.get("resume")

        if not resume:
            return Response(
                {"detail": "Resume file is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_resume_file(resume)
        except ValidationError as exc:
            return Response(
                {"detail": exc.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check for duplicate resume
        new_hash = compute_file_hash(resume)

        if candidate.resume:
            try:
                existing_hash = compute_file_hash(
                    candidate.resume.file
                )

                if existing_hash == new_hash:
                    return Response(
                        {
                            "detail": (
                                "This resume is already uploaded."
                            ),
                            "resume": candidate.resume.url,
                        },
                        status=status.HTTP_200_OK,
                    )

            except (FileNotFoundError, ValueError):
                pass

        old_resume = candidate.resume

        # Generate a safe unique filename
        extension = resume.name.rsplit(".", 1)[-1].lower()

        import uuid

        filename = (
            f"resume_{candidate.id}_"
            f"{uuid.uuid4().hex}.{extension}"
        )

        resume.name = filename

        candidate.resume = resume
        candidate.save(update_fields=["resume"])

        # Delete previous resume after successful replacement
        if old_resume:
            try:
                old_resume.delete(save=False)
            except Exception:
                pass

        resume_url = request.build_absolute_uri(
            candidate.resume.url
        )

        return Response(
            {
                "message": "Resume uploaded successfully.",
                "resume": resume_url,
                "filename": candidate.resume.name,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# ADMIN PROFILE MANAGEMENT
# ============================================================

class AdminEmployerVerifyView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def post(self, request, pk):
        if request.user.role != User.Role.ADMIN:
            return Response(
                {"detail": "Only admins can verify employers."},
                status=status.HTTP_403_FORBIDDEN,
            )

        employer = get_object_or_404(
            Employer,
            pk=pk,
        )

        employer.is_company_verified = True
        employer.save(
            update_fields=["is_company_verified"]
        )

        return Response(
            {
                "message": (
                    "Employer company verified successfully."
                ),
                "employer_id": employer.id,
                "is_company_verified": (
                    employer.is_company_verified
                ),
            },
            status=status.HTTP_200_OK,
        )


class AdminRestoreProfileView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def post(self, request, kind, pk):
        if request.user.role != User.Role.ADMIN:
            return Response(
                {"detail": "Only admins can restore profiles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if kind == "candidate":
            profile = get_object_or_404(
                Candidate,
                pk=pk,
            )

        elif kind == "employer":
            profile = get_object_or_404(
                Employer,
                pk=pk,
            )

        else:
            return Response(
                {
                    "detail": (
                        "Invalid profile type. "
                        "Use candidate or employer."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile.is_deleted = False
        profile.save(update_fields=["is_deleted"])

        return Response(
            {
                "message": (
                    f"{kind.capitalize()} profile restored."
                ),
                "profile_id": profile.id,
                "is_deleted": profile.is_deleted,
            },
            status=status.HTTP_200_OK,
        )