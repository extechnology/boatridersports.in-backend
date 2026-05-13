from rest_framework.permissions import BasePermission
from Application.AuthenticationServices.auth_utils import get_user_from_request


class IsUserAuthenticated(BasePermission):
    def has_permission(self, request, view):
        return bool(get_user_from_request(request))

class IsSuperUserAuthenticated(BasePermission):
    def has_permission(self, request, view):
        user= request.user 
        if not user:
            user = get_user_from_request(request)
        print(user)
        return bool(user and user.is_superuser)