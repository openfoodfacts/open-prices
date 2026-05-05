from rest_framework.permissions import SAFE_METHODS, BasePermission


def request_user_is_object_owner(request, obj) -> bool:
    return (
        request.user
        and request.user.is_authenticated
        and (obj.owner == request.user.user_id)
    )


def request_user_is_moderator(request) -> bool:
    return request.user and request.user.is_authenticated and request.user.is_moderator


class OnlyObjectOwnerIsAllowedWrite(BasePermission):
    """
    - Gives read access to everyone
    - Gives write access ONLY to object owners
    """

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return request_user_is_object_owner(request, obj)


class OnlyObjectOwnerIsAllowedReadWrite(BasePermission):
    """
    - Gives read access ONLY to object owners
    - Gives write access ONLY to object owners
    """

    def has_object_permission(self, request, view, obj):
        return request_user_is_object_owner(request, obj)


class OnlyObjectOwnerOrModeratorIsAllowedWrite(BasePermission):
    """
    - Gives read access to everyone
    - Gives write access ONLY to object owners or moderators
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return request_user_is_object_owner(request, obj) or request_user_is_moderator(
            request
        )


class OnlyObjectOwnerOrModeratorIsAllowedReadWrite(BasePermission):
    """
    - Gives read access ONLY to object owners or moderators
    - Gives write access ONLY to object owners or moderators
    """

    def has_object_permission(self, request, view, obj):
        return request_user_is_object_owner(request, obj) or request_user_is_moderator(
            request
        )


class OnlyModeratorIsAllowedReadWrite(BasePermission):
    """
    - Gives read access ONLY to moderators
    - Gives write access ONLY to moderators
    """

    def has_permission(self, request, view):
        return request_user_is_moderator(request)
