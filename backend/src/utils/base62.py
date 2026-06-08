import random
import string

BASE62_ALPHABET = string.ascii_letters + string.digits  # a-zA-Z0-9 (len 62)

def generate_short_code(length: int = 7) -> str:
    """Generate a random Base62 string of specified length."""
    return "".join(random.choices(BASE62_ALPHABET, k=length))
