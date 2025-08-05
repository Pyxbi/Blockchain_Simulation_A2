import time
import logging
import queue
from transaction import Transaction
from models import Block
from consensus import Consensus
from wallet import create_wallet as wallet_create_wallet
from schema import validate_transaction_dict, validate_block_dict
from persistence import Persistence
from p2p import P2P

class Blockchain(Persistence, P2P):
    """
    Unified Blockchain class: integrates persistence, P2P, consensus, wallet, and schema validation.
    """
    def __init__(self):
        super().__init__()
        self.chain = []  # List[Block]
        self.pending_transactions = []  # List[Transaction]
        self.difficulty = 4  # Initial difficulty
        self.target_block_time = 10  # Target block time in seconds
        self.balances = {}  # Dict[str, float]
        self.wallets = {}  # Dict[str, private_key_hex]
        self.public_keys = {}  # Dict[str, public_key_hex]
        self.nodes = []  # List[Blockchain]
        self.transaction_queue = queue.Queue()
        self.block_queue = queue.Queue()
        self.load_from_disk()
        if not self.chain:
            self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(
            mined_by="genesis",
            transactions=[],
            height=0,
            difficulty=self.difficulty,
            hash="",
            previous_hash="0",
            nonce=0,
            timestamp=int(time.time()),
        )
        genesis_block.hash = genesis_block.calculate_hash()
        self.chain.append(genesis_block)
        self.save_to_disk()
        logging.info("Genesis block created")

    def get_latest_block(self):
        return self.chain[-1]

    def get_balance(self, address):
        """Get the current balance for a given address."""
        return self.balances.get(address, 0)

    def add_transaction(self, tx):
        """Add a transaction to the pending pool after verifying signature, balance, and schema validation."""
        try:
            validate_transaction_dict(tx.to_dict())
        except Exception as e:
            logging.warning(f"Transaction schema validation failed: {e}")
            return False
        if not tx.verify():
            logging.warning("Transaction signature invalid")
            return False
        sender_balance = self.balances.get(tx.sender, 0)
        if sender_balance < tx.amount:
            logging.warning("Insufficient balance for transaction")
            return False
        total_pending = sum(t.amount for t in self.pending_transactions if t.sender == tx.sender)
        if sender_balance - total_pending < tx.amount:
            logging.warning("Double-spend attempt detected in pending pool")
            return False
        self.pending_transactions.append(tx)
        self.save_to_disk()
        return True

    def mine_block(self, miner_address):
        """Mine a new block with pending transactions and reward the miner using Consensus. Save to disk after mining."""
        if not self.pending_transactions:
            logging.info("No transactions to mine.")
            return None
        last_block = self.get_latest_block()
        block = Consensus.proof_of_work(
            last_block=last_block,
            transactions=self.pending_transactions,
            miner_address=miner_address,
            difficulty=self.difficulty
        )
        try:
            validate_block_dict(block.to_dict())
        except Exception as e:
            logging.error(f"Block validation failed: {e}")
            return None
        self.chain.append(block)
        for tx in block.transactions:
            if tx.sender != "COINBASE":
                self.balances[tx.sender] = self.balances.get(tx.sender, 0) - tx.amount
            self.balances[tx.recipient] = self.balances.get(tx.recipient, 0) + tx.amount
        self.pending_transactions = []
        self.difficulty = Consensus.adjust_difficulty(
            self.chain,
            target_block_time=self.target_block_time,
            adjustment_interval=10,
            min_difficulty=1
        )
        self.save_to_disk()
        logging.info(f"Block #{block.height} mined by {miner_address} with hash {block.hash}")
        return block

    def is_valid_block(self, block: Block, previous_block: Block = None):
        if previous_block is None:
            previous_block = self.get_latest_block()
        if block.hash != block.calculate_hash():
            logging.error(f"Invalid block hash for block #{block.height}")
            return False
        if block.previous_hash != previous_block.hash:
            logging.error(f"Invalid previous hash for block #{block.height}")
            return False
        if not block.hash.startswith("0" * block.difficulty):
            logging.error(f"Block #{block.height} does not meet difficulty requirement")
            return False
        if block.height != previous_block.height + 1:
            logging.error(f"Invalid block height for block #{block.height}")
            return False
        return True

    def is_valid_chain(self, chain=None):
        chain = chain or self.chain
        if not chain:
            return False
        if chain[0].height != 0 or chain[0].previous_hash != "0":
            logging.error("Invalid genesis block")
            return False
        for i in range(1, len(chain)):
            current = chain[i]
            previous = chain[i-1]
            if current.hash != current.calculate_hash():
                logging.error(f"Invalid hash in block #{current.height}")
                return False
            if current.previous_hash != previous.hash:
                logging.error(f"Chain broken at block #{current.height}")
                return False
            if not current.hash.startswith("0" * current.difficulty):
                logging.error(f"Difficulty not met in block #{current.height}")
                return False
            if current.height != previous.height + 1:
                logging.error(f"Invalid height sequence at block #{current.height}")
                return False
        return True

    def create_wallet(self, initial_balance: float = 100.0):
        address, private_key_hex, public_key_hex = wallet_create_wallet()
        self.wallets[address] = private_key_hex
        self.public_keys[address] = public_key_hex
        if initial_balance > 0:
            self.balances[address] = initial_balance
        return address, private_key_hex, public_key_hex

    def sync_chain(self):
        for node in self.nodes:
            if len(node.chain) > len(self.chain) and node.is_valid_chain():
                for block in node.chain:
                    try:
                        validate_block_dict(block.to_dict())
                    except Exception as e:
                        logging.error(f"Block validation failed during sync: {e}")
                        return False
                self.chain = node.chain[:]
                self.rebuild_balances()
                self.save_to_disk()
                logging.info("Chain synchronized with longer valid chain")
                return True
        return False

    def rebuild_balances(self):
        self.balances.clear()
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender != "COINBASE":
                    self.balances[tx.sender] = self.balances.get(tx.sender, 0) - tx.amount
                self.balances[tx.recipient] = self.balances.get(tx.recipient, 0) + tx.amount