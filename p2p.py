import logging
import queue
import threading
import time
import requests
from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from models import Block
from transaction import Transaction
import socketio

class P2PNode:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.peers = set()
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, async_mode='eventlet')
        self.transaction_queue = queue.Queue()
        self.block_queue = queue.Queue()
        self._setup_routes()

    def _setup_routes(self):
        """Defines the Flask routes and SocketIO events for P2P communication."""
        @self.app.route('/chain', methods=['GET'])
        def get_chain():
            chain_data = [block.to_dict() for block in self.chain]
            return jsonify({'length': len(chain_data), 'chain': chain_data}), 200

        @self.app.route('/transaction', methods=['POST'])
        def receive_transaction():
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No transaction data provided'}), 400
                
                tx = Transaction.from_dict(data)
                logging.info(f"Node {self.port} received new transaction {tx.signature[:8]}... via HTTP.")
                
                # Before processing, sync our chain to get latest balances
                self.sync_chain()
                
                # Add to transaction queue for processing
                self.transaction_queue.put(tx)
                return jsonify({'message': 'Transaction received successfully'}), 201
            except Exception as e:
                logging.error(f"Error receiving transaction: {e}")
                return jsonify({'error': str(e)}), 400

        @self.app.route('/block', methods=['POST'])
        def receive_block():
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No block data provided'}), 400
                
                block = Block.from_dict(data)
                logging.info(f"Node {self.port} received new block #{block.height} via HTTP.")
                
                # Add to block queue for processing
                self.block_queue.put(block)
                return jsonify({'message': 'Block received successfully'}), 201
            except Exception as e:
                logging.error(f"Error receiving block: {e}")
                return jsonify({'error': str(e)}), 400

        @self.app.route('/add_peer', methods=['POST'])
        def add_peer():
            data = request.get_json()
            if not data or 'peer_url' not in data:
                return jsonify({'error': 'Invalid peer URL provided'}), 400
            peer_url = data['peer_url']
            self.peers.add(peer_url)
            logging.info(f"Node {self.port} connected to new peer: {peer_url}")
            return jsonify({'message': 'Peer added successfully', 'peers': list(self.peers)}), 201

        @self.socketio.on('new_block')
        def handle_new_block(block_data):
            try:
                block = Block.from_dict(block_data)
                logging.info(f"Node {self.port} received new block #{block.height} via WebSocket.")
                self.block_queue.put(block)
            except Exception as e:
                logging.error(f"Error handling new block event: {e}")

        @self.socketio.on('new_transaction')
        def handle_new_transaction(tx_data):
            try:
                tx = Transaction.from_dict(tx_data)
                logging.info(f"Node {self.port} received new transaction {tx.signature[:8]}... via WebSocket.")
                self.transaction_queue.put(tx)
            except Exception as e:
                logging.error(f"Error handling new transaction event: {e}")

    def run(self):
        """Starts the node's server and background queue processor."""
        self._start_queue_processor()
        logging.info(f"🚀 Starting node server at http://{self.host}:{self.port}")
        self.socketio.run(self.app, host=self.host, port=self.port, use_reloader=False)

    def connect_to_peer(self, peer_url):
        """Connects this node to a new peer."""
        if peer_url != f"http://{self.host}:{self.port}":
            self.peers.add(peer_url)
            try:
                requests.post(f"{peer_url}/add_peer", json={'peer_url': f"http://{self.host}:{self.port}"})
                logging.info(f"Node {self.port} successfully connected to peer {peer_url}")
            except requests.exceptions.RequestException as e:
                logging.warning(f"Node {self.port} could not connect to peer {peer_url}: {e}")

    def broadcast_transaction(self, transaction: Transaction):
        """Broadcasts a transaction to all connected peers via HTTP and SocketIO."""
        logging.info(f"Node {self.port} broadcasting transaction to {len(self.peers)} peers.")
        for peer_url in self.peers:
            try:
                # Send via HTTP POST to the peer's transaction endpoint
                response = requests.post(f"{peer_url}/transaction", 
                                       json=transaction.to_dict(), 
                                       timeout=5)
                if response.status_code == 201:
                    logging.info(f"Node {self.port}: Successfully sent transaction to {peer_url}")
                else:
                    logging.warning(f"Node {self.port}: Failed to send transaction to {peer_url}: {response.status_code}")
            except Exception as e:
                logging.error(f"Node {self.port}: Failed to broadcast transaction to {peer_url}: {e}")

    def broadcast_block(self, block: Block):
        """Broadcasts a newly mined block to all connected peers via HTTP."""
        logging.info(f"Node {self.port} broadcasting block #{block.height} to {len(self.peers)} peers.")
        for peer_url in self.peers:
            try:
                # Send via HTTP POST to the peer's block endpoint
                response = requests.post(f"{peer_url}/block", 
                                       json=block.to_dict(), 
                                       timeout=5)
                if response.status_code == 201:
                    logging.info(f"Node {self.port}: Successfully sent block to {peer_url}")
                else:
                    logging.warning(f"Node {self.port}: Failed to send block to {peer_url}: {response.status_code}")
            except Exception as e:
                logging.error(f"Node {self.port}: Failed to broadcast block to {peer_url}: {e}")

    def sync_chain(self):
        """Synchronizes the chain with the longest valid chain from peers."""
        logging.info(f"Node {self.port} starting chain synchronization...")
        # (This method is now part of the Blockchain class as it needs access to self.chain)
        super().sync_chain() # We call the method on the parent class (Blockchain)

    def _start_queue_processor(self):
        """Runs the block and transaction queue processing in a background thread."""
        def process_queues():
            # Timer for proactive, periodic sync
            last_sync_time = time.time()
            
            while True:
                # --- 1. REACTIVE SYNC (Your existing logic) ---
                # This handles blocks that arrive out of order during normal operation.
                try:
                    block = self.block_queue.get_nowait()
                    # If we receive a block that's ahead of us, we know we're behind.
                    if block.height > len(self.chain):
                         logging.info(f"Node {self.port}: Received future block #{block.height}. Triggering chain sync.")
                         self.sync_chain()
                    # If the block is the very next one, add it.
                    elif self.is_valid_block(block) and block.hash not in [b.hash for b in self.chain]:
                        self.chain.append(block)
                        # Remove mined transactions from the pending pool
                        self.pending_transactions = [tx for tx in self.pending_transactions if tx.signature not in [t.signature for t in block.transactions]]
                        self.rebuild_balances()
                        self.save_to_disk()
                        logging.info(f"P2P: Node {self.port} added block #{block.height} from peer.")
                except queue.Empty:
                    pass # It's normal for the queue to be empty.
                except Exception as e:
                    logging.error(f"P2P Error processing block queue: {e}")

                # --- (Your transaction processing logic is fine here) ---
                try:
                    tx = self.transaction_queue.get_nowait()
                    if tx.signature not in [t.signature for t in self.pending_transactions]:
                        if tx.verify():
                            self.pending_transactions.append(tx)
                            logging.info(f"P2P: Transaction {tx.signature[:8]}... added to pending pool from peer.")
                except queue.Empty:
                    pass
                except Exception as e:
                    logging.error(f"P2P Error processing transaction queue: {e}")
                
                # --- 2. PROACTIVE SYNC (The self-healing mechanism) ---
                # Every 60 seconds, proactively ask peers if they have a longer chain.
                # This is what allows a node to catch up after being offline.
                if time.time() - last_sync_time > 60:
                    logging.info(f"Node {self.port}: Performing periodic automatic chain synchronization.")
                    self.sync_chain()
                    last_sync_time = time.time() # Reset the timer

                time.sleep(0.1) # Prevents the loop from using 100% CPU

        processing_thread = threading.Thread(target=process_queues, daemon=True)
        processing_thread.start()