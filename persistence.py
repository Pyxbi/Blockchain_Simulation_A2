import json
import os
import logging
from transaction import Transaction
from models import Block
from nacl.signing import SigningKey, VerifyKey

class Persistence:
    def save_to_disk(self):
        """Save blockchain state to disk using new class-based structures."""
        try:
            # Convert wallets and public keys to saveable format
            wallets_hex = self.wallets.copy()
            public_keys_hex = self.public_keys.copy()

            # Include initial wallet balances if available
            save_data = {
                'chain': [block.to_dict() for block in self.chain],
                'balances': self.balances,
                'wallets': wallets_hex,
                'public_keys': public_keys_hex
            }
            
            # Save initial wallet balances if they exist
            if hasattr(self, 'initial_wallet_balances'):
                save_data['initial_wallet_balances'] = self.initial_wallet_balances

            with open('blockchain.json', 'w') as f:
                json.dump(save_data, f)
            logging.info("Blockchain state saved to disk")
        except Exception as e:
            logging.error(f"Failed to save blockchain state: {e}")

    def load_from_disk(self):
        """Load blockchain state from disk using new class-based structures."""
        if os.path.exists('blockchain.json'):
            try:
                with open('blockchain.json', 'r') as f:
                    data = json.load(f)
                    self.chain = []
                    for block_data in data['chain']:
                        transactions = [Transaction.from_dict(tx) for tx in block_data['transactions']]
                        block = Block(
                            mined_by=block_data['mined_by'],
                            transactions=transactions,
                            height=block_data['height'],
                            difficulty=block_data['difficulty'],
                            hash=block_data['hash'],
                            previous_hash=block_data['previous_hash'],
                            nonce=block_data['nonce'],
                            timestamp=block_data['timestamp'],
                            merkle_root=block_data.get('merkle_root')
                        )
                        self.chain.append(block)
                    self.balances = data.get('balances', {})
                    
                    # Load initial wallet balances if available
                    if 'initial_wallet_balances' in data:
                        self.initial_wallet_balances = data['initial_wallet_balances']
                    else:
                        self.initial_wallet_balances = {}
                    
                    # Load wallets and public keys if available
                    if 'wallets' in data and 'public_keys' in data:
                        self.wallets = {}
                        self.public_keys = {}
                        for addr, private_key_hex in data['wallets'].items():
                            try:
                                private_key = SigningKey(bytes.fromhex(private_key_hex))
                                self.wallets[addr] = private_key
                            except Exception as e:
                                logging.warning(f"Failed to load private key for {addr}: {e}")
                        for addr, public_key_hex in data['public_keys'].items():
                            try:
                                public_key = VerifyKey(bytes.fromhex(public_key_hex))
                                self.public_keys[addr] = public_key
                            except Exception as e:
                                logging.warning(f"Failed to load public key for {addr}: {e}")
                        logging.info(f"Loaded {len(self.wallets)} wallets from disk")
                    logging.info("Blockchain state loaded from disk")
            except Exception as e:
                logging.error(f"Failed to load blockchain state: {e}")
                # If loading fails, remove the corrupted file and start fresh
                try:
                    os.remove('blockchain.json')
                    logging.info("Corrupted blockchain file removed, starting fresh")
                except:
                    pass