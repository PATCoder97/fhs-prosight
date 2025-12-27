from authlib.integrations.starlette_client import OAuth
from app.core.config import settings

oauth = OAuth()

oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

class GoogleAuthClient:
    def __init__(self):
        self.client = oauth.google

    async def get_authorization_url(self, request):
        redirect_uri = request.url_for("google_callback")
        return await self.client.authorize_redirect(request, redirect_uri)

    async def get_user_info(self, request):
        token = await self.client.authorize_access_token(request)
        userinfo = token.get("userinfo")
        return {
            "token": token,
            "userinfo": userinfo
        }
