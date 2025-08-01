import hashlib
import json

class Block:
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
        self.difficulty = difficulty
        self.hash = hash
        self.previous_hash = previous_hash
        self.nonce = nonce
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
        }, sort_keys=True)
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

class Peer:
    def __init__(self, ip, port, last_seen):
        self.ip = ip
        self.port = port
        self.last_seen = last_seen