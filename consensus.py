import json
import time
from models import Block
from transaction import Transaction

class Consensus:
    @staticmethod
    def valid_proof(block: Block, difficulty: int) -> bool:
        """Check if a block's hash meets the difficulty requirement."""
        return block.hash.startswith("0" * difficulty)

    @staticmethod
    def proof_of_work(last_block: Block, transactions, miner_address, difficulty: int, reward_amount=10):
        """
        Perform proof-of-work to mine a new block.
        Returns the mined Block.
        """
        height = last_block.height + 1
        previous_hash = last_block.hash
        timestamp = int(time.time())
        # Add mining reward transaction
        reward_tx = Transaction(
            sender="COINBASE",
            recipient=miner_address,
            amount=reward_amount,
            timestamp=timestamp
        )
        txs = transactions.copy() + [reward_tx]
       # Create block with nonce=0 initially
        block = Block(
            mined_by=miner_address,
            transactions=txs,
            height=height,
            difficulty=difficulty,
            hash="",  # Will be computed
            previous_hash=previous_hash,
            nonce=0,
            timestamp=timestamp
        )

        # Proof-of-work loop
        while True:
            block.hash = block.calculate_hash()

            # Debug print to see the block string and hash for each nonce:
            block_string = json.dumps({
                'mined_by': block.mined_by,
                'transactions': [tx if isinstance(tx, dict) else tx.to_dict(include_signature=True) for tx in block.transactions],
                'height': block.height,
                'difficulty': block.difficulty,
                'previous_hash': block.previous_hash,
                'nonce': block.nonce,
                'timestamp': block.timestamp,
                'merkle_root': block.merkle_root
            }, sort_keys=True)

            print(f"[Mining] Nonce: {block.nonce} Hash: {block.hash}")
            print(f"[Mining] Block String for hash:\n{block_string}\n")
            if Consensus.valid_proof(block, difficulty):
                return block
            block.nonce += 1   

    @staticmethod
    def adjust_difficulty(chain, target_block_time=10, adjustment_interval=10, min_difficulty=1):
        """
        Adjust mining difficulty based on the time taken to mine the last N blocks.
        """
        length = len(chain)
        if length < adjustment_interval + 1:
            return chain[-1].difficulty if chain else min_difficulty
        last_adjustment_block = chain[-adjustment_interval-1]
        latest_block = chain[-1]
        actual_time = latest_block.timestamp - last_adjustment_block.timestamp
        expected_time = adjustment_interval * target_block_time
        difficulty = latest_block.difficulty
        if actual_time < expected_time / 2:
            difficulty += 1
        elif actual_time > expected_time * 2 and difficulty > min_difficulty:
            difficulty -= 1
        return difficulty