from django.contrib.auth.backends import BaseBackend
from msal import ConfidentialClientApplication
import requests
from .models import CustomUser

class AzureADB2CBackend(BaseBackend):
    def authenticate(self, request, code):
        # Initialize the ConfidentialClientApplication
        app = ConfidentialClientApplication(
            request.META['AUTH_AZURE_AD_B2C']['CLIENT_ID'],
            client_credential=request.META['AUTH_AZURE_AD_B2C']['CLIENT_SECRET'],
            authority=f'https://login.microsoftonline.com/tfp/{request.META["AUTH_AZURE_AD_B2C"]["TENANT"]}/{request.META["AUTH_AZURE_AD_B2C"]["POLICY_NAME"]}/v2.0'
        )

        # Acquire a token by authorization code
        token = app.acquire_token_by_authorization_code(code, ['openid'])

        # Decode the token and get user information
        user_info = requests.get(
            f'https://graph.microsoft.com/v1.0/me',
            headers={'Authorization': f'Bearer {token["access_token"]}'}
        ).json()

        # Get or create the user in the CustomUser model
        user, _ = CustomUser.objects.get_or_create(
            email=user_info['mail'],
            defaults={
                'first_name': user_info['givenName'],
                'last_name': user_info['surname'],
            }
        )

        return user

    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None