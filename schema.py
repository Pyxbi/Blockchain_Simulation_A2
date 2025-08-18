import hashlib
import json
from marshmallow import Schema, fields, validates_schema, ValidationError, post_load
from transaction import Transaction
from models import Block

class TransactionSchema(Schema):
    sender = fields.Str(required=True)
    recipient = fields.Str(required=True)
    amount = fields.Float(required=True)
    timestamp = fields.Int(required=True)
    signature = fields.Str(required=False, allow_none=True)

    @post_load
    def make_transaction(self, data, **kwargs):
        return Transaction(**data)

class BlockSchema(Schema):
    mined_by = fields.Str(required=True)
    transactions = fields.Nested(TransactionSchema, many=True)
    height = fields.Int(required=True)
    difficulty = fields.Int(required=True)
    hash = fields.Str(required=True)
    previous_hash = fields.Str(required=True)
    nonce = fields.Int(required=True)
    timestamp = fields.Int(required=True)
    merkle_root = fields.Str(required=True)

    @post_load
    def make_block(self, data, **kwargs):
        # The 'transactions' are already converted to Transaction objects by the nested schema
        return Block(**data)

    @validates_schema
    def validate_hash(self, data, **kwargs):
        """
        Validates the hash of the block directly from the incoming data dictionary.
        """
        # --- FIXED LOGIC ---
        # 1. Take a copy of the data dictionary to avoid modifying the original
        block_data_for_hashing = data.copy()
        
        # 2. The 'hash' field itself is not part of the data used to calculate the hash
        provided_hash = block_data_for_hashing.pop('hash', None)

        # 3. Create the canonical block string from the rest of the data
        # This must exactly match the logic in your Block.calculate_hash() method
        # Handle both cases: transactions as dicts or Transaction objects
        transactions_data = []
        for tx in block_data_for_hashing['transactions']:
            if isinstance(tx, dict):
                transactions_data.append(tx)
            else:
                # It's a Transaction object, convert to dict
                transactions_data.append(tx.to_dict())
        
        block_string = json.dumps({
            'mined_by': block_data_for_hashing['mined_by'],
            'transactions': transactions_data,
            'height': block_data_for_hashing['height'],
            'difficulty': block_data_for_hashing['difficulty'],
            'previous_hash': block_data_for_hashing['previous_hash'],
            'nonce': block_data_for_hashing['nonce'],
            'timestamp': block_data_for_hashing['timestamp'],
            'merkle_root': block_data_for_hashing['merkle_root']
        }, sort_keys=True).encode('utf-8')

        # 4. Calculate the hash and compare
        calculated_hash = hashlib.sha256(block_string).hexdigest()

        if provided_hash != calculated_hash:
            raise ValidationError(
                f"Block hash is invalid. Expected: {calculated_hash}, Got: {provided_hash}"
            )

# --- Usage Helpers (Unchanged) ---
def validate_transaction_dict(tx_dict):
    """Validates and deserializes a transaction dictionary."""
    schema = TransactionSchema()
    return schema.load(tx_dict)

def validate_block_dict(block_dict):
    """Validates and deserializes a block dictionary."""
    schema = BlockSchema()
    return schema.load(block_dict)