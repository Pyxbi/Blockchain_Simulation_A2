import time
import logging
from marshmallow import ValidationError
import requests
from persistence import Persistence
from p2p import P2PNode 
from models import Block
import schema
from transaction import Transaction
from consensus import Consensus
from wallet import generate_wallet as wallet_create_wallet


class Blockchain(P2PNode, Persistence):
    transaction_schema = schema.TransactionSchema()
    block_schema = schema.BlockSchema()
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
        self.initial_balance_txs = []  # Store initial balance transactions for genesis

        self.load_from_disk()
        if not self.chain:
            self.create_genesis_block()

    def create_wallet(self, initial_balance: float = 100.0):
        address, private_key_hex, public_key_hex = wallet_create_wallet()
        self.wallets[address] = private_key_hex
        self.public_keys[address] = public_key_hex
        
        # Store the initial balance separately to never lose it
        if not hasattr(self, 'initial_wallet_balances'):
            self.initial_wallet_balances = {}
        self.initial_wallet_balances[address] = initial_balance
        
        # Set current balance
        self.balances[address] = initial_balance
        logging.info(f"Created wallet {address[:10]}... with initial balance {initial_balance}")
            
        return address, private_key_hex, public_key_hex

    def create_genesis_block(self):
        genesis_block = Block(
            mined_by="genesis",
            transactions=self.initial_balance_txs,
            height=0,
            difficulty=self.difficulty,
            hash="",
            previous_hash="0",
            nonce=0,
            timestamp=int(time.time()),
        )
        genesis_block.hash = genesis_block.calculate_hash()
        self.chain.append(genesis_block)
        
        # Rebuild balances to include initial wallet balances from genesis block
        self.rebuild_balances()
        
        self.save_to_disk()
        logging.info("Genesis block created")

    def get_latest_block(self):
        return self.chain[-1]

    def get_balance(self, address):
        """Get the current balance for a given address, checking both address and public key."""
        # First check if the address itself has a balance
        if address in self.balances:
            return self.balances[address]
        
        # If not found, check if this address has a corresponding public key with balance
        if address in self.public_keys:
            public_key = self.public_keys[address]
            if public_key in self.balances:
                return self.balances[public_key]
        
        # If the input is a public key, check if it has a corresponding address
        for addr, pub_key in self.public_keys.items():
            if pub_key == address and addr in self.balances:
                return self.balances[addr]
        
        return 0

    def add_transaction(self, tx: Transaction):
        """Adds a transaction to the pending pool after full validation."""
        try:
            validated_tx = self.transaction_schema.validate_transaction_dict(tx.to_dict())

            if not validated_tx.verify():
                raise ValueError("Transaction signature invalid")
            
            # Convert sender public key to address for balance checking
            pubkey_to_address = {pub: addr for addr, pub in self.public_keys.items()}
            print(f"Validated sender: {validated_tx.sender}")
            print(f"Known public keys: {list(pubkey_to_address.keys())}")
            
            if validated_tx.sender not in pubkey_to_address:
                raise ValueError("Sender public key not recognized")
            
            sender_addr = pubkey_to_address.get(validated_tx.sender, validated_tx.sender)

            if self.get_balance(sender_addr) < validated_tx.amount:
                raise ValueError("Insufficient balance")
            
            # Double spend check in pending pool - check by sender address
            pending_spend = sum(t.amount for t in self.pending_transactions 
                              if pubkey_to_address.get(t.sender, t.sender) == sender_addr)
            
            print(f"Validated sender: {validated_tx.sender}")
            print(f"Known public keys: {list(pubkey_to_address.keys())}")
            print(f"Sender addr: {sender_addr}")
            print(f"Balance: {self.get_balance(sender_addr)}")
            print(f"Pending spend: {pending_spend}")

            
            if self.get_balance(sender_addr) - pending_spend < tx.amount:
                raise ValueError("Double-spend attempt detected in pending pool")

            self.pending_transactions.append(tx)
            logging.info(f"Transaction {tx.signature[:8]} added to pending pool.")
            self.save_to_disk()
            return True
        except Exception as e:
            logging.warning(f"Transaction failed validation: {e}")
            return False

    def mine_block(self, miner_identifier):
        """Mines a new block with exactly 1 transaction, rewards the miner, and updates the chain."""
        if not self.pending_transactions:
            logging.info("No transactions to mine.")
            return False
        
        is_valid_chain, message = self.is_valid_chain()
        if not is_valid_chain:
            logging.error(f"Cannot mine block: Invalid chain - {message}")
            return False

        # Convert miner identifier to address if it's a public key
        pubkey_to_address = {pub: addr for addr, pub in self.public_keys.items()}
        miner_address = pubkey_to_address.get(miner_identifier, miner_identifier)
        
        # Ensure we have a valid wallet address for the miner
        # if miner_address not in self.wallets:
        #     logging.error(f"Invalid miner address: {miner_address}")
        #     return False

            # Accept external public keys not in self.wallets
        if miner_address not in self.wallets and miner_identifier not in pubkey_to_address:
            # Check if miner_identifier looks like a valid public key (64 hex chars)
            if isinstance(miner_identifier, str) and len(miner_identifier) == 64:
                miner_address = miner_identifier  # Use raw public key as reward address
            else:
                logging.error(f"Invalid miner identifier: {miner_identifier}")
                return False

        last_block = self.get_latest_block()
        #select exactly 1 transaction for the block
        selected_transaction = self.pending_transactions[0]
        if not selected_transaction:
            logging.info("No valid transaction available for mining.")
            return False

        # Only pass the user transaction(s) to Consensus; reward is handled there
        transactions_to_mine = [selected_transaction]

        block = Consensus.proof_of_work(
            last_block=last_block,
            transactions=transactions_to_mine,
            miner_address=miner_address,  # Always pass the wallet address
            difficulty=self.difficulty
        )
        try:
            validated_block = self.block_schema.validate_block_dict(block.to_dict())
        except ValidationError as e:
            logging.error(f"Block validation failed: {e.messages}")
            return False  
        # Add the valid block to the chain
        self.chain.append(validated_block)


        # Remove ONLY the transaction that was actually mined
        mined_user_transactions = [tx for tx in validated_block.transactions if tx.sender != "COINBASE"]
        if mined_user_transactions:
            mined_tx = mined_user_transactions[0]  # Should be exactly 1
            self.pending_transactions = [
                tx for tx in self.pending_transactions 
                if tx.signature != mined_tx.signature
            ]
            logging.info(f"Removed transaction {mined_tx.signature[:8]}... from mempool. {len(self.pending_transactions)} transactions remain.")

        self.rebuild_balances()

        # Adjust difficulty for the next block
        self.difficulty = Consensus.adjust_difficulty(self.chain)
        self.save_to_disk()
        logging.info(f"Block #{validated_block.height} mined successfully with 1 transaction by {miner_address[:10]}...")
        return validated_block

    def is_valid_block(self, block: Block, previous_block: Block = False):
        if previous_block is False:
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

    def is_valid_chain(self, chain=False):
        chain = chain or self.chain
        if not chain:
            return False, "Empty chain"
        if chain[0].height != 0 or chain[0].previous_hash != "0":
            return False, "Invalid genesis block"
        for i in range(1, len(chain)):
            current = chain[i]
            previous = chain[i-1]
            if current.hash != current.calculate_hash():
                return False, f"Invalid hash in block #{current.height}"
            if current.previous_hash != previous.hash:
                return False, f"Chain broken at block #{current.height}"
            if not current.hash.startswith("0" * current.difficulty):
                return False, f"Difficulty not met in block #{current.height}"
            if current.height != previous.height + 1:
                return False, f"Invalid height sequence at block #{current.height}"
            if current.timestamp <= previous.timestamp:
                return False,f"Invalid timestamp for block #{current.height}. Must be after previous block."
        return True, "OK"


    def sync_chain(self):
        """Synchronizes the chain by fetching and validating chains from peers."""
        longest_chain = False
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
        """Rebuild balances from the entire blockchain, handling both addresses and public keys."""
        logging.info("Starting balance rebuild...")
        
        # Build mapping dictionaries for both directions
        pubkey_to_address = {pub: addr for addr, pub in self.public_keys.items()}
        address_to_pubkey = {addr: pub for addr, pub in self.public_keys.items()}
        logging.info(f"Address to public key mapping: {len(self.public_keys)} entries")
        
        # Initialize all known wallet addresses with their original initial balances
        self.balances.clear()
        
        # Ensure we have initial_wallet_balances attribute
        if not hasattr(self, 'initial_wallet_balances'):
            self.initial_wallet_balances = {}
            # For existing wallets, assume 100 coins initial balance
            for address in self.wallets.keys():
                self.initial_wallet_balances[address] = 100.0
        
        for address in self.wallets.keys():
            initial_balance = self.initial_wallet_balances.get(address, 100.0)
            self.balances[address] = initial_balance
            logging.info(f"  Initialized {address[:8]}... with initial balance {initial_balance}")
        
        # Process all transactions in the blockchain
        for block in self.chain:
            logging.info(f"Processing block #{block.height} with {len(block.transactions)} transactions")
            for tx in block.transactions:
                
                # Handle sender (debit) - only for non-COINBASE transactions
                if tx.sender != "COINBASE":
                    # Convert sender (usually public key) to address
                    sender_addr = pubkey_to_address.get(tx.sender, tx.sender)
                    if sender_addr in self.balances:
                        old_balance = self.balances[sender_addr]
                        self.balances[sender_addr] = old_balance - tx.amount
                        logging.info(f"  Deducted {tx.amount} from {sender_addr[:8]}... (was {old_balance}, now {self.balances[sender_addr]})")
                    else:
                        logging.warning(f"  Unknown sender {sender_addr[:8]}... for debit of {tx.amount}")
                
                # Handle recipient (credit) - for all transactions
                recipient_addr = False
                
                if tx.sender == "COINBASE":
                    # For COINBASE, recipient should be an address (mining reward)
                    if tx.recipient in self.wallets:
                        # Recipient is an address
                        recipient_addr = tx.recipient
                        logging.info(f"  COINBASE recipient is wallet address: {recipient_addr[:8]}...")
                    elif tx.recipient in pubkey_to_address:
                        # Recipient is a public key, convert to address
                        recipient_addr = pubkey_to_address[tx.recipient]
                        logging.info(f"  COINBASE recipient converted from pubkey to address: {recipient_addr[:8]}...")
                    else:
                        # Unknown recipient - might be external address
                        recipient_addr = tx.recipient
                        logging.warning(f"  Unknown COINBASE recipient {tx.recipient[:8]}...")
                else:
                    # For regular transactions, recipient is usually a public key
                    if tx.recipient in pubkey_to_address:
                        # Recipient is a public key, convert to address
                        recipient_addr = pubkey_to_address[tx.recipient]
                        logging.info(f"  Regular transaction recipient converted from pubkey to address: {recipient_addr[:8]}...")
                    elif tx.recipient in self.wallets:
                        # Recipient is an address
                        recipient_addr = tx.recipient
                        logging.info(f"  Regular transaction recipient is wallet address: {recipient_addr[:8]}...")
                    else:
                        # Unknown recipient
                        recipient_addr = tx.recipient
                        logging.warning(f"  Unknown transaction recipient {tx.recipient[:8]}...")
                
                # Credit the recipient
                if recipient_addr:
                    old_balance = self.balances.get(recipient_addr, 0)
                    self.balances[recipient_addr] = old_balance + tx.amount
                    logging.info(f"  Credited {tx.amount} to {recipient_addr[:8]}... (was {old_balance}, now {self.balances[recipient_addr]})")
        
        # Final cleanup: ensure all wallets have entries
        for address in self.wallets.keys():
            if address not in self.balances:
                initial_balance = self.initial_wallet_balances.get(address, 100.0)
                self.balances[address] = initial_balance
                logging.info(f"  Restored missing balance for {address[:8]}... to {initial_balance}")
        
        logging.info(f"Balance rebuild complete. Final balances: {self.balances}")