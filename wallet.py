import hashlib
from nacl.signing import SigningKey
from nacl.encoding import HexEncoder

def create_wallet():
    """Generate a new Ed25519 public/private key pair and return (address, private_key_hex, public_key_hex)."""
    private_key = SigningKey.generate()
    public_key = private_key.verify_key
    address = hashlib.sha256(public_key.encode()).hexdigest()
    return address, private_key.encode(encoder=HexEncoder).decode(), public_key.encode(encoder=HexEncoder).decode()