
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import SignupView, LoginView, LogoutView, MeView
from .rbac_views import (
    JobListCreateView,
    JobDetailView,
    ApplicationCreateView,
    MyApplicationsView,
    ApplicationDetailView,
    VerifyUserView,
)


urlpatterns = [
    path("auth/signup/", SignupView.as_view(), name="signup"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me/", MeView.as_view(), name="me"),

    path("jobs/", JobListCreateView.as_view(), name="job-list-create"),
    path("jobs/<int:pk>/", JobDetailView.as_view(), name="job-detail"),

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

    path(
        "admin-tools/verify-user/<int:user_id>/",
        VerifyUserView.as_view(),
        name="verify-user",
    ),
]
