from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    SignupView,
    LoginView,
    LogoutView,
    MeView,
    MyCandidateProfileView,
    CandidateProfileDetailView,
    MyEmployerProfileView,
    EmployerProfileDetailView,
    AdminEmployerVerifyView,
    AdminRestoreProfileView,
    ResumeUploadView,
)

from .rbac_views import (
    JobListCreateView,
    JobDetailView,
    ApplicationCreateView,
    MyApplicationsView,
    ApplicationDetailView,
    VerifyUserView,
)


urlpatterns = [
    # Authentication
    path("auth/signup/", SignupView.as_view(), name="signup"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me/", MeView.as_view(), name="me"),

    # Jobs
    path(
        "jobs/",
        JobListCreateView.as_view(),
        name="job-list-create",
    ),
    path(
        "jobs/<int:pk>/",
        JobDetailView.as_view(),
        name="job-detail",
    ),

    # Applications
    path(
        "applications/",
        ApplicationCreateView.as_view(),
        name="application-create",
    ),
    path(
        "applications/mine/",
        MyApplicationsView.as_view(),
        name="application-mine",
    ),
    path(
        "applications/<int:pk>/",
        ApplicationDetailView.as_view(),
        name="application-detail",
    ),

    # Candidate profile
    path(
        "profile/candidate/me/",
        MyCandidateProfileView.as_view(),
        name="candidate-profile-me",
    ),
    path(
        "profile/candidate/<int:pk>/",
        CandidateProfileDetailView.as_view(),
        name="candidate-profile-detail",
    ),

    # Resume
    path(
        "profile/candidate/resume/",
        ResumeUploadView.as_view(),
        name="candidate-resume-upload",
    ),

    # Employer profile
    path(
        "profile/employer/me/",
        MyEmployerProfileView.as_view(),
        name="employer-profile-me",
    ),
    path(
        "profile/employer/<int:pk>/",
        EmployerProfileDetailView.as_view(),
        name="employer-profile-detail",
    ),

    # Admin profile actions
    path(
        "profile/employer/<int:pk>/verify/",
        AdminEmployerVerifyView.as_view(),
        name="employer-profile-verify",
    ),
    path(
        "profile/<str:kind>/<int:pk>/restore/",
        AdminRestoreProfileView.as_view(),
        name="profile-restore",
    ),
    path(
        "admin-tools/verify-user/<int:user_id>/",
        VerifyUserView.as_view(),
        name="verify-user",
    ),
]