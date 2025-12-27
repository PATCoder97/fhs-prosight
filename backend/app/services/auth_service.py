from app.integrations import GoogleAuthClient
from app.schemas import GoogleLoginResponse, SocialLoginUser
from app.core.jwt_handler import create_access_token

google_auth = GoogleAuthClient()


async def get_google_auth_url(request):
    return await google_auth.get_authorization_url(request)


async def handle_google_callback(request) -> GoogleLoginResponse:
    userinfo = await google_auth.get_user_info(request)

    # Tạo token truy cập cho người dùng
    access_token = create_access_token(
        user_id=userinfo.get("sub"),
        full_name=userinfo.get("name"),
        role="user",
        scope="access",
    )

    # Format response theo schema
    user = SocialLoginUser(
        id=userinfo.get("sub"),
        email=userinfo.get("email"),
        full_name=userinfo.get("name"),
        avatar=userinfo.get("picture"),
        role="user",
        is_new_user=False,
    )

    response = GoogleLoginResponse(
        access_token=access_token, token_type="bearer", user=user
    )

    return response
