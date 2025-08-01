import json
import time
from nacl.signing import SigningKey, VerifyKey
from nacl.encoding import HexEncoder
from nacl.exceptions import BadSignatureError

class Transaction:
    def __init__(self, sender, recipient, amount, timestamp=None, signature=None):
        self.sender = sender  # public key (hex string)
        self.recipient = recipient  # public key (hex string)
        self.amount = amount
        self.timestamp = timestamp or int(time.time())
        self.signature = signature  # hex string

    def to_dict(self, include_signature=True):
        d = {
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "timestamp": self.timestamp,
        }
        if include_signature and self.signature:
            d["signature"] = self.signature
        return d

    def sign(self, private_key_hex):
        """Sign the transaction with the sender's private key (hex string)."""
        tx_dict = self.to_dict(include_signature=False)
        tx_bytes = json.dumps(tx_dict, sort_keys=True).encode("utf-8")
        signing_key = SigningKey(private_key_hex, encoder=HexEncoder)
        signature = signing_key.sign(tx_bytes).signature
        self.signature = HexEncoder.encode(signature).decode("utf-8")

    def verify(self):
        """Verify the transaction's signature using the sender's public key."""
        if not self.signature:
            return False
        tx_dict = self.to_dict(include_signature=False)
        tx_bytes = json.dumps(tx_dict, sort_keys=True).encode("utf-8")
        try:
            verify_key = VerifyKey(self.sender, encoder=HexEncoder)
            verify_key.verify(tx_bytes, HexEncoder.decode(self.signature))
            return True
        except BadSignatureError:
            return False

    @classmethod
    def from_dict(cls, d):
        return cls(
            sender=d["sender"],
            recipient=d["recipient"],
            amount=d["amount"],
            timestamp=d.get("timestamp"),
            signature=d.get("signature"),
        )