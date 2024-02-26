from passlib.context import CryptContext

from src.config.manager import settings


class HashGenerator:
    _hash_ctx_layer_1: CryptContext = CryptContext(
        schemes=[settings.HASHING_ALGORITHM_LAYER_1], deprecated="auto"
    )
    _hash_ctx_layer_2: CryptContext = CryptContext(
        schemes=[settings.HASHING_ALGORITHM_LAYER_2], deprecated="auto"
    )
    _hash_ctx_salt: str = settings.HASHING_SALT

    @classmethod
    def _get_hashing_salt(cls) -> str:
        return cls._hash_ctx_salt

    @classmethod
    def generate_password_salt_hash(cls) -> str:
        """
        A function to generate a hash from Bcrypt to append to the user password.
        """
        return cls._hash_ctx_layer_1.hash(secret=cls._get_hashing_salt())

    @classmethod
    def generate_password_hash(cls, hash_salt: str, password: str) -> str:
        """
        A function that adds the user's password with the layer 1 Bcrypt hash, before
        hash it for the second time using Argon2 algorithm.
        """
        return cls._hash_ctx_layer_2.hash(secret=hash_salt + password)

    @classmethod
    def is_password_verified(cls, password: str, hashed_password: str) -> bool:
        """
        A function that decodes users' password and verifies whether it is the correct password.
        """
        return cls._hash_ctx_layer_2.verify(secret=password, hash=hashed_password)


class PasswordGenerator:
    @classmethod
    def generate_salt(cls) -> str:
        return HashGenerator.generate_password_salt_hash()

    @classmethod
    def generate_hashed_password(cls, hash_salt: str, new_password: str) -> str:
        return HashGenerator.generate_password_hash(hash_salt=hash_salt, password=new_password)

    @classmethod
    def is_password_authenticated(cls, hash_salt: str, password: str, hashed_password: str) -> bool:
        return HashGenerator.is_password_verified(password=hash_salt + password, hashed_password=hashed_password)
