from app.integrations import GoogleAuthClient
from app.schemas.auth import GoogleLoginResponse, SocialLoginUser

google_auth = GoogleAuthClient()

async def get_google_auth_url(request):
    return await google_auth.get_authorization_url(request)

async def handle_google_callback(request) -> GoogleLoginResponse:
    data = await google_auth.get_user_info(request)
    token = data.get("token")
    userinfo = data.get("userinfo")
    
    # Format response theo schema
    user = SocialLoginUser(
        id=userinfo.get("sub"),
        email=userinfo.get("email"),
        full_name=userinfo.get("name"),
        avatar=userinfo.get("picture"),
        provider="google",
        role="user",
        is_new_user=False
    )
    
    response = GoogleLoginResponse(
        access_token=token.get("access_token"),
        refresh_token=token.get("refresh_token"),
        token_type="bearer",
        expires_in=token.get("expires_in", 86400),
        scope="access",
        user=user
    )
    
    return response
