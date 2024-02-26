from fastapi import HTTPException, status

async def http_exc_400_credentials_bad_signup_request() -> Exception:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Signup failed! Recheck all your credentials!",
    )


async def http_exc_400_credentials_bad_signin_request() -> Exception:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Signin failed! Invalid username or password!",
    )


async def http_exc_400_req_body_bad_signin_request() -> Exception:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Signin failed! Make sure that all data is correct and code has not expired",
    )


async def http_400_exc_bad_username_request(username: str) -> Exception:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"The username {username} is taken! Be creative and choose another one!",
    )


async def http_400_exc_bad_email_request(email: str) -> Exception:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"The email {email} is already registered! Be creative and choose another one!",
    )


async def http_exc_400_client_credentials_bad_request() -> Exception:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Signin failed! Check your client credentials.",
    )
