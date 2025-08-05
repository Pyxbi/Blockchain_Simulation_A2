import logging
import time
import threading
import queue
from transaction import Transaction
from models import Block
from schema import validate_block_dict

class P2P:
    def broadcast_transaction(self, transaction: Transaction):
        """Broadcast transaction to other nodes."""
        if not self.nodes:
            logging.info("No P2P nodes to broadcast transaction to")
            return
        
        try:
            for node in self.nodes:
                if hasattr(node, 'transaction_queue'):
                    node.transaction_queue.put(transaction)
            logging.info(f"Transaction broadcasted to {len(self.nodes)} nodes")
        except Exception as e:
            logging.error(f"Error broadcasting transaction: {e}")

    def broadcast_block(self, block: Block):
        """Broadcast block to other nodes."""
        if not self.nodes:
            logging.info("No P2P nodes to broadcast block to")
            return
            
        try:
            for node in self.nodes:
                if hasattr(node, 'block_queue'):
                    node.block_queue.put(block)
            logging.info(f"Block #{block.height} broadcasted to {len(self.nodes)} nodes")
        except Exception as e:
            logging.error(f"Error broadcasting block: {e}")

    def sync_chain(self):
        """Synchronize with the longest valid chain from other nodes."""
        if not self.nodes:
            return False
            
        try:
            for node in self.nodes:
                if len(node.chain) > len(self.chain) and node.is_valid_chain():
                    # Validate all blocks in the new chain before accepting
                    valid_chain = True
                    for block in node.chain:
                        try:
                            validate_block_dict(block.to_dict())
                        except Exception as e:
                            logging.error(f"Block validation failed during sync: {e}")
                            valid_chain = False
                            break
                    
                    if valid_chain:
                        self.chain = node.chain[:]
                        self.rebuild_balances()
                        self.save_to_disk()
                        logging.info(f"Chain synchronized with longer valid chain ({len(self.chain)} blocks)")
                        return True
        except Exception as e:
            logging.error(f"Error during chain synchronization: {e}")
        
        return False


    def start_node(self):
        """Start processing transactions and blocks from queues."""
        def process_queues():
            while True:
                try:
                    # Process incoming transactions
                    try:
                        tx = self.transaction_queue.get_nowait()
                        if tx not in self.pending_transactions:  # Avoid duplicates
                            # Enhanced balance synchronization for received transactions
                            sender_addr = None
                            recipient_addr = None
                            
                            # Find addresses corresponding to sender and recipient public keys
                            for addr, pub_key in self.public_keys.items():
                                if pub_key == tx.sender:
                                    sender_addr = addr
                                if pub_key == tx.recipient:
                                    recipient_addr = addr
                            
                            # Sync sender balance if we have this wallet
                            if sender_addr and sender_addr in self.balances:
                                if tx.sender not in self.balances:
                                    self.balances[tx.sender] = self.balances[sender_addr]
                                elif self.balances[tx.sender] != self.balances[sender_addr]:
                                    # Sync the balances to avoid inconsistencies
                                    self.balances[tx.sender] = self.balances[sender_addr]
                            
                            # Sync recipient balance if we have this wallet
                            if recipient_addr and recipient_addr in self.balances:
                                if tx.recipient not in self.balances:
                                    self.balances[tx.recipient] = self.balances[recipient_addr]
                            
                            # Suppress logging during P2P transaction processing to avoid CLI interruption
                            old_level = logging.getLogger().level
                            logging.getLogger().setLevel(logging.ERROR)
                            try:
                                success = self.add_transaction(tx)
                                if success:
                                    logging.getLogger().setLevel(old_level)
                                    logging.info(f"P2P: Received and added transaction from {tx.sender[:8]}... to {tx.recipient[:8]}...")
                                    logging.getLogger().setLevel(logging.ERROR)
                            except Exception as e:
                                logging.getLogger().setLevel(old_level)
                                logging.warning(f"P2P: Failed to process transaction: {e}")
                                logging.getLogger().setLevel(logging.ERROR)
                            finally:
                                logging.getLogger().setLevel(old_level)
                    except queue.Empty:
                        pass
                    except Exception as e:
                        logging.error(f"P2P: Error processing transaction queue: {e}")

                    # Process incoming blocks
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
                            logging.info(f"P2P: Received and added block #{block.height}")
                        elif block.height < len(self.chain):
                            # Block is older than our current chain, ignore
                            pass
                        elif block.height > len(self.chain):
                            # Block is ahead of us, try to sync
                            logging.info(f"P2P: Received future block #{block.height}, attempting sync...")
                            self.sync_chain()
                    except queue.Empty:
                        pass
                    except Exception as e:
                        logging.error(f"P2P: Error processing block queue: {e}")

                except Exception as e:
                    logging.error(f"P2P: Unexpected error in queue processing: {e}")
                
                time.sleep(0.1)

        # Start the processing thread
        processing_thread = threading.Thread(target=process_queues, daemon=True)
        processing_thread.start()
        logging.info("P2P node started successfully")
