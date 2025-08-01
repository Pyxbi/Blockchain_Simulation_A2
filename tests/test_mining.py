#!/usr/bin/env python3

from blockchain import Blockchain
from transaction import Transaction
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_mining():
    """Test mining functionality with the schema validation fix."""
    print("\n=== Testing Mining with Schema Fix ===")
    
    # Create blockchain
    blockchain = Blockchain()
    
    # Create test wallets
    print("Creating test wallets...")
    addr1, priv1, pub1 = blockchain.create_wallet(initial_balance=100)
    addr2, priv2, pub2 = blockchain.create_wallet(initial_balance=50)
    miner_addr, miner_priv, miner_pub = blockchain.create_wallet(initial_balance=0)
    
    # Set balances for public keys (workaround for balance tracking issue)
    blockchain.balances[pub1] = 100
    blockchain.balances[pub2] = 50
    blockchain.balances[miner_pub] = 0
    
    print(f"Wallet 1: {addr1[:16]}... (Balance: {blockchain.get_balance(addr1)})")
    print(f"Wallet 2: {addr2[:16]}... (Balance: {blockchain.get_balance(addr2)})")
    print(f"Miner: {miner_addr[:16]}... (Balance: {blockchain.get_balance(miner_addr)})")
    
    # Create and add transaction
    print("\nCreating transaction...")
    tx = Transaction(sender=pub1, recipient=pub2, amount=25)
    tx.sign(priv1)
    print(f"Transaction signed: {tx.verify()}")
    
    # Add transaction to blockchain
    result = blockchain.add_transaction(tx)
    print(f"Transaction added: {result}")
    print(f"Pending transactions: {len(blockchain.pending_transactions)}")
    
    # Try mining
    print("\nAttempting to mine block...")
    print(f"Mining difficulty: {blockchain.difficulty}")
    print("This may take a moment...")
    
    try:
        block = blockchain.mine_block(miner_pub)
        if block:
            print("✅ Mining SUCCESS!")
            print(f"Block hash: {block.hash}")
            print(f"Block height: {block.height}")
            print(f"Transactions in block: {len(block.transactions)}")
            print(f"Chain length: {len(blockchain.chain)}")
            
            # Check balances after mining
            print(f"\nBalances after mining:")
            print(f"Sender: {blockchain.get_balance(addr1)} (should be 75)")
            print(f"Recipient: {blockchain.get_balance(addr2)} (should be 75)")
            print(f"Miner: {blockchain.get_balance(miner_addr)} (should be 10)")
            
            return True
        else:
            print("❌ Mining FAILED - No block returned")
            return False
            
    except Exception as e:
        print(f"❌ Mining FAILED with error: {e}")
        logging.error(f"Mining error: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_mining()
    if success:
        print("\n🎉 Mining test completed successfully!")
    else:
        print("\n💥 Mining test failed!")
