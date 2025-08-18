import hashlib
import json
from transaction import Transaction

class Block:
    """Represents a single block in the blockchain."""
    def __init__(
        self,
        mined_by,
        transactions,
        height,
        difficulty,
        hash,
        previous_hash,
        nonce,
        timestamp,
        merkle_root=None
    ):
        self.mined_by = mined_by
        self.transactions = transactions  # List of transaction dicts or Transaction objects
        self.height = height  # Also known as index
        self.difficulty = difficulty # Mining difficulty for this block
        self.hash = hash
        self.previous_hash = previous_hash
        self.nonce = nonce # Nonce for proof-of-work
        self.timestamp = timestamp
        self.merkle_root = merkle_root or self.calculate_merkle_root() 

    def calculate_merkle_root(self):
        """
        Calculate the Merkle root of the transactions in this block.
        Transactions should be a list of dicts or objects with a to_dict() method.
        """
        tx_hashes = [
            hashlib.sha256(json.dumps(tx if isinstance(tx, dict) else tx.to_dict(), sort_keys=True).encode()).hexdigest()
            for tx in self.transactions
        ]
        if not tx_hashes:
            return hashlib.sha256(b'').hexdigest()
        while len(tx_hashes) > 1:
            if len(tx_hashes) % 2 == 1:
                tx_hashes.append(tx_hashes[-1])  # duplicate last hash if odd number
            tx_hashes = [
                hashlib.sha256((tx_hashes[i] + tx_hashes[i+1]).encode()).hexdigest()
                for i in range(0, len(tx_hashes), 2)
            ]
        return tx_hashes[0]

    def calculate_hash(self):
        """
        Calculate the block's SHA-256 hash from all critical fields.
        """
        block_string = json.dumps({
            'mined_by': self.mined_by,
            'transactions': [tx if isinstance(tx, dict) else tx.to_dict() for tx in self.transactions],
            'height': self.height,
            'difficulty': self.difficulty,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'timestamp': self.timestamp,
            'merkle_root': self.merkle_root
        }, sort_keys=True) # Convert to JSON string with sorted keys
        # Calculate the SHA-256 hash of the block string
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self):
        """
        Serialize the block to a dictionary for JSON export.
        """
        return {
            'mined_by': self.mined_by,
            'transactions': [tx if isinstance(tx, dict) else tx.to_dict() for tx in self.transactions],
            'height': self.height,
            'difficulty': self.difficulty,
            'hash': self.hash,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'timestamp': self.timestamp,
            'merkle_root': self.merkle_root
        }
    # In your Block class
    @classmethod
    def from_dict(cls, data):
        # Convert transaction dicts back to Transaction objects
        transactions = [Transaction.from_dict(tx) for tx in data.get('transactions', [])]
        return cls(
            mined_by=data['mined_by'],
            transactions=transactions,
            height=data['height'],
            difficulty=data['difficulty'],
            hash=data['hash'],
            previous_hash=data['previous_hash'],
            nonce=data['nonce'],
            timestamp=data['timestamp'],
            merkle_root=data.get('merkle_root')
        )

class Peer:
    def __init__(self, ip, port, last_seen):
        self.ip = ip
        self.port = port
        self.last_seen = last_seen