from integrations import GoogleAuthClient

google_auth = GoogleAuthClient()

async def get_google_auth_url(request):
    return await google_auth.get_authorization_url(request)

async def handle_google_callback(request):
    return await google_auth.get_user_info(request)
