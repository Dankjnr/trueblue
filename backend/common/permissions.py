from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    message = "Only administrators may perform this action."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "admin")


class IsCleaner(BasePermission):
    message = "Only cleaners may perform this action."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "cleaner")


class IsCustomer(BasePermission):
    message = "Only customers may perform this action."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "customer")


class IsAdminOrReadOwn(BasePermission):
    """
    Admins may access anything. Non-admins may only access objects that
    belong to them, as determined by the view's `get_owner(obj)` -> user
    comparison. Enforced at the object level, never trusting client input
    such as query params for whose data is being fetched.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role == "admin":
            return True
        owner = getattr(view, "get_owner", lambda o: None)(obj)
        return owner is not None and owner.pk == user.pk
