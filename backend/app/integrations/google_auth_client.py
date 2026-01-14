from authlib.integrations.starlette_client import OAuth
from app.core.config import settings

oauth = OAuth()

oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


class GoogleAuthClient:
    def __init__(self):
        self.client = oauth.google

    def _get_redirect_uri(self, request):
        """
        Generate correct redirect URI with proper scheme (http/https).
        Handles reverse proxy scenarios (Cloudflare, nginx, etc.)
        """
        # Get base redirect URI from FastAPI
        redirect_uri = str(request.url_for("google_callback"))

        # Check if behind reverse proxy with HTTPS
        # Cloudflare and most reverse proxies set X-Forwarded-Proto header
        forwarded_proto = request.headers.get("x-forwarded-proto")
        if forwarded_proto == "https":
            redirect_uri = redirect_uri.replace("http://", "https://")

        return redirect_uri

    async def get_authorization_url(self, request):
        redirect_uri = self._get_redirect_uri(request)
        return await self.client.authorize_redirect(request, redirect_uri)

    async def get_user_info(self, request):
        token = await self.client.authorize_access_token(request)
        return token.get("userinfo")
