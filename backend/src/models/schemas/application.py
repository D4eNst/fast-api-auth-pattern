import pydantic
from passlib.pwd import genword

from src.models.schemas.base import BaseSchemaModel


class SApplication(BaseSchemaModel):
    user: int
    name: str
    description: str = ""
    website: str
    redirect_uris: list
    allowed_users: list[dict[str, str]] | None = None
    mode: str = 'dev'
    client_id: str = None
    client_secret: str = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.client_id is None:
            self.client_id = genword(entropy=64, length=32)
        if self.client_secret is None:
            client_secret = genword(entropy=64, length=32)
            self.client_secret = genword(entropy=64, length=32)
