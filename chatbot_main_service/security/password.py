from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """
    Hashes a plain text password using Argon2.
    """

    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verifies a plain text password against its hash.
    """

    return password_hash.verify(password, hashed_password)