from fastapi import HTTPException, status


async def http_403_exc_forbidden_request() -> Exception:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Refused access to the requested resource!",
    )


async def http_403_forbidden_inactive_user() -> Exception:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Account is inactive!"
    )
