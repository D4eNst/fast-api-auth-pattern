from fastapi import HTTPException, status


async def http_exc_401_unauthorized_request() -> Exception:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Refused to complete request due to lack of valid authentication!",
    )


async def http_401_exc_bad_token_request() -> Exception:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"Invalid token!",
    )


async def http_401_exc_expired_token_request() -> Exception:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"Token has expired!",
    )


async def http_401_exc_not_enough_permissions() -> Exception:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not enough permissions"
    )
