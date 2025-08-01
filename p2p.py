import logging
import time
import threading
import queue
from transaction import Transaction
from models import Block

class P2P:
    def broadcast_transaction(self, transaction: Transaction):
        """Broadcast transaction to other nodes."""
        for node in self.nodes:
            node.transaction_queue.put(transaction)
        logging.info("Transaction broadcasted to nodes")

    def broadcast_block(self, block: Block):
        """Broadcast block to other nodes."""
        for node in self.nodes:
            node.block_queue.put(block)
        logging.info(f"Block #{block.height} broadcasted to nodes")

    def sync_chain(self):
        """Synchronize with the longest valid chain from other nodes."""
        for node in self.nodes:
            if len(node.chain) > len(self.chain) and node.is_valid_chain():
                self.chain = node.chain[:]
                self.rebuild_balances()
                self.save_to_disk()
                logging.info("Chain synchronized with longer valid chain")


    def start_node(self):
        """Start processing transactions and blocks from queues."""
        def process_queues():
            while True:
                try:
                    tx = self.transaction_queue.get_nowait()
                    if tx not in self.pending_transactions:  # Avoid duplicates
                        # Ensure balance synchronization for received transactions
                        # Find the address corresponding to the sender public key
                        sender_addr = None
                        for addr, pub_key in self.public_keys.items():
                            if pub_key == tx.sender:
                                sender_addr = addr
                                break
                        
                        # Sync balances if we have this wallet
                        if sender_addr and sender_addr in self.balances:
                            if tx.sender not in self.balances:
                                self.balances[tx.sender] = self.balances[sender_addr]
                            elif self.balances[tx.sender] < tx.amount:
                                self.balances[tx.sender] = self.balances[sender_addr]
                        
                        # Suppress logging during P2P transaction processing to avoid CLI interruption
                        old_level = logging.getLogger().level
                        logging.getLogger().setLevel(logging.ERROR)
                        try:
                            self.add_transaction(tx)
                        finally:
                            logging.getLogger().setLevel(old_level)
                except queue.Empty:
                    pass

                try:
                    block = self.block_queue.get_nowait()
                    if (block.height == len(self.chain) and 
                        self.is_valid_block(block) and 
                        block not in self.chain):
                        self.chain.append(block)
                        # Remove transactions that are now in the block
                        for tx in block.transactions:
                            if tx in self.pending_transactions:
                                self.pending_transactions.remove(tx)
                        self.rebuild_balances()
                        self.save_to_disk()
                        logging.info(f"Received and added block #{block.height}")
                except queue.Empty:
                    pass

                time.sleep(0.1)

        threading.Thread(target=process_queues, daemon=True).start()
