from rest_framework.permissions import SAFE_METHODS, BasePermission


class OnlyOwnerCanEditOrDelete(BasePermission):
    """
    Only allow owners to edit or delete an object.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return (
            request.user
            and request.user.is_authenticated
            and (obj.owner == request.user.user_id)
        )


class OnlyOwnerOrModeratorCanEditOrDelete(BasePermission):
    """
    Only allow owners or moderators to edit or delete an object.
    - only for non-safe methods
    - (use only for Price or Proof objects)
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return (
            request.user
            and request.user.is_authenticated
            and ((obj.owner == request.user.user_id) or request.user.is_moderator)
        )
