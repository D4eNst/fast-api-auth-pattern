from fastapi import HTTPException, status


async def http_404_exc_email_not_found_request(email: str) -> Exception:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Either the account with email `{email}` doesn't exist, has been deleted, or you are not authorized!",
    )


async def http_404_exc_id_not_found_request(id: int) -> Exception:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Either the object with id `{id}` doesn't exist, has been deleted, or you are not authorized!",
    )


async def http_404_exc_username_not_found_request(username: str) -> Exception:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Either the account with username `{username}` doesn't exist, has been deleted, or you are not "
               f"authorized!",
    )
