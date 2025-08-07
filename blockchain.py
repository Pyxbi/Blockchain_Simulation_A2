import time
import logging
import requests
from persistence import Persistence
from p2p import P2PNode 
from models import Block
from transaction import Transaction
from consensus import Consensus
from wallet import create_wallet as wallet_create_wallet
from schema import validate_transaction_dict, validate_block_dict

class Blockchain(P2PNode, Persistence):
    """
    Core Blockchain class. Manages the chain, transactions, and consensus,
    while inheriting P2P and Persistence functionality.
    """
    def __init__(self, host='127.0.0.1', port=5000):
        # Initialize the P2P and Persistence parent classes
        P2PNode.__init__(self, host, port)
        Persistence.__init__(self)

        # Core blockchain attributes
        self.chain = []
        self.pending_transactions = []
        self.difficulty = 4
        self.target_block_time = 10
        self.balances = {}
        self.wallets = {}
        self.public_keys = {}

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

    def add_transaction(self, tx: Transaction):
        """Adds a transaction to the pending pool after full validation."""
        try:
            validate_transaction_dict(tx.to_dict())
            if not tx.verify():
                raise ValueError("Transaction signature invalid")
            if self.get_balance(tx.sender) < tx.amount:
                raise ValueError("Insufficient balance")
            # Double spend check in pending pool
            pending_spend = sum(t.amount for t in self.pending_transactions if t.sender == tx.sender)
            if self.get_balance(tx.sender) - pending_spend < tx.amount:
                raise ValueError("Double-spend attempt detected in pending pool")

            self.pending_transactions.append(tx)
            logging.info(f"Transaction {tx.signature[:8]} added to pending pool.")
            return True
        except Exception as e:
            logging.warning(f"Transaction failed validation: {e}")
            return False

    def mine_block(self, miner_address):
        """Mines a new block, rewards the miner, and updates the chain."""
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
            self.chain.append(block)
            # Update balances and clear pending transactions
            self.rebuild_balances()
            self.pending_transactions = []
            self.difficulty = Consensus.adjust_difficulty(self.chain)
            self.save_to_disk()
            logging.info(f"Block #{block.height} mined successfully by {miner_address[:10]}...")
            return block
        except Exception as e:
            logging.error(f"Mined block failed validation: {e}")
            return None

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
        """Synchronizes the chain by fetching and validating chains from peers."""
        longest_chain = None
        max_length = len(self.chain)

        for peer_url in self.peers:
            try:
                response = requests.get(f'{peer_url}/chain')
                if response.status_code == 200:
                    data = response.json()
                    length = data['length']
                    if length > max_length:
                        peer_chain = [Block.from_dict(b) for b in data['chain']]
                        if self.is_valid_chain(peer_chain):
                             max_length = length
                             longest_chain = peer_chain
            except requests.exceptions.RequestException as e:
                logging.warning(f"Could not sync with peer {peer_url}: {e}")

        if longest_chain:
            self.chain = longest_chain
            self.rebuild_balances()
            self.save_to_disk()
            logging.info(f"Chain synchronized to length {len(self.chain)}")

    def rebuild_balances(self):
        self.balances.clear()
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender != "COINBASE":
                    self.balances[tx.sender] = self.balances.get(tx.sender, 0) - tx.amount
                self.balances[tx.recipient] = self.balances.get(tx.recipient, 0) + tx.amount