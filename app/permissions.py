from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import User


class IsAdmin(BasePermission):
    message = "Only admins can perform this action."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Role.ADMIN)


class IsEmployer(BasePermission):
    message = "Only employers can perform this action."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Role.EMPLOYER)


class IsCandidate(BasePermission):
    message = "Only candidates can perform this action."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Role.CANDIDATE)


class IsOwnerEmployer(BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return bool(
            request.user.is_authenticated
            and request.user.role == User.Role.EMPLOYER
            and obj.employer.user_id == request.user.id
        )


class IsOwnerCandidate(BasePermission):
    message = "You can only access your own applications."

    def has_object_permission(self, request, view, obj):
        return bool(
            request.user.is_authenticated
            and request.user.role == User.Role.CANDIDATE
            and obj.candidate.user_id == request.user.id
        )