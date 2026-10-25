from rest_framework.permissions import BasePermission


class StaffPermission(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and request.user.is_active
            and request.user.role in ("cashier", "manager")
        )


class ManagerPermission(StaffPermission):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == "manager"
