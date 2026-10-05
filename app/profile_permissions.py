from rest_framework.permissions import BasePermission

from .models import User


class IsSelfOrAdmin(BasePermission):
   
    message = "You can only access your own profile."

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        if request.user.role == User.Role.ADMIN:
            return True
        return obj.user_id == request.user.id