import hashlib
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey

def generate_wallet():
    private_key = SigningKey.generate()
    public_key = private_key.verify_key

    private_key_hex = private_key.encode(encoder=HexEncoder).decode()
    public_key_hex = public_key.encode(encoder=HexEncoder).decode()

    # Generate address (e.g., SHA256 hash of public key)
    address = hashlib.sha256(public_key.encode()).hexdigest()

    return address, private_key_hex, public_key_hex



