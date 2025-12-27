from authlib.integrations.starlette_client import OAuth
from app.core.config import settings

oauth = OAuth()

oauth.register(
    name='github',
    client_id=settings.GITHUB_CLIENT_ID,
    client_secret=settings.GITHUB_CLIENT_SECRET,
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'read:user user:email'},
)


class GitHubAuthClient:
    def __init__(self):
        self.client = oauth.github

    async def get_authorization_url(self, request):
        redirect_uri = request.url_for("github_callback")
        return await self.client.authorize_redirect(request, redirect_uri)

    async def get_user_info(self, request):
        token = await self.client.authorize_access_token(request)
        resp = await self.client.get("user", token=token)
        return resp.json()
