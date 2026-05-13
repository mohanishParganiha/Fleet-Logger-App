""" Here you define Custom permissions for users."""
from rest_framework.permissions import BasePermission


class IsManager(BasePermission):
    """
    custome permission for manager
    """

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and getattr(
                request.user, 'is_manager', False)
        )
