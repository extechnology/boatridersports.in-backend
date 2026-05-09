# myapp/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # Look for access_token in cookies
        access_token = request.COOKIES.get("access_token")
        if not access_token:
            return None

        # Validate the token using SimpleJWT logic
        validated_token = self.get_validated_token(access_token)
        return self.get_user(validated_token), validated_token