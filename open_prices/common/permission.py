from rest_framework.permissions import SAFE_METHODS, BasePermission


def request_user_is_object_owner(request, obj) -> bool:
    return (
        request.user
        and request.user.is_authenticated
        and (obj.owner == request.user.user_id)
    )


def request_user_is_moderator(request) -> bool:
    return request.user and request.user.is_authenticated and request.user.is_moderator


class OnlyObjectOwnerIsAllowed(BasePermission):
    """
    Only give access to object owners.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return request_user_is_object_owner(request, obj)


class OnlyObjectOwnerOrModeratorIsAllowed(BasePermission):
    """
    Only give access to object owners or moderators.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return request_user_is_object_owner(request, obj) or request_user_is_moderator(
            request
        )


class OnlyModeratorIsAllowed(BasePermission):
    """
    Only give access to moderators.
    """

    def has_permission(self, request, view):
        return request_user_is_moderator(request)
