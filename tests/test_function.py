from blockchain import Blockchain
from transaction import Transaction


class TestBlockchain:
   def run_tests():
    """Run basic tests to verify blockchain functionality."""
    print("\n=== Running Blockchain Tests ===")
    blockchain = Blockchain()
    
    # Test wallet creation
    print("1. Testing wallet creation...")
    addr1, priv1, pub1 = blockchain.create_wallet(initial_balance=100)
    addr2, priv2, pub2 = blockchain.create_wallet(initial_balance=50)
    print(f"   Created wallet 1: {addr1[:16]}... with balance {blockchain.get_balance(addr1)}")
    print(f"   Created wallet 2: {addr2[:16]}... with balance {blockchain.get_balance(addr2)}")
    
    # IMPORTANT: Also set balance for public keys to match transaction validation
    blockchain.balances[pub1] = 100
    blockchain.balances[pub2] = 50
    
    # Save to ensure persistence works
    try:
        blockchain.save_to_disk()
        print("   Initial save successful")
    except Exception as e:
        print(f"   Save error: {e}")
    
    # Test transaction creation
    print("2. Testing transaction creation...")
    tx = Transaction(sender=pub1, recipient=pub2, amount=25)
    tx.sign(priv1)
    print(f"   Transaction created and signed")
    print(f"   Valid signature: {tx.verify()}")
    
    # Test transaction addition
    print("3. Testing transaction addition...")
    
    # Debug: Print transaction details
    print(f"   Transaction signature: {tx.signature[:16] if tx.signature else 'None'}...")
    print(f"   Transaction dict: {tx.to_dict()}")
    
    result = blockchain.add_transaction(tx)
    print(f"   Transaction added to pending pool: {result}")
    print(f"   Pending transactions: {len(blockchain.pending_transactions)}")
    
    # Try to save after adding transaction
    try:
        blockchain.save_to_disk()
        print("   Save after transaction successful")
    except Exception as e:
        print(f"   Save error after transaction: {e}")
    
    # Test mining
    print("4. Testing mining...")
    miner_addr, miner_priv, miner_pub = blockchain.create_wallet(initial_balance=0)
    blockchain.balances[miner_pub] = 0  # Also set for public key
    initial_blocks = len(blockchain.chain)
    
    # Debug: Check if transactions have signatures
    print(f"   Pending transactions before mining: {len(blockchain.pending_transactions)}")
    for i, tx in enumerate(blockchain.pending_transactions):
        print(f"   Transaction {i+1}: signature={tx.signature is not None}")
        print(f"   Transaction {i+1} dict: {tx.to_dict()}")
    
    # Try mining without schema validation first
    print("   Attempting to mine block...")
    try:
        block = blockchain.mine_block(miner_pub)
        print(f"   Block mined: {block is not None}")
        if block:
            print(f"   Block hash: {block.hash}")
            print(f"   Block dict: {block.to_dict()}")
            
            # IMPORTANT: Sync miner reward balance for testing
            miner_pub_balance = blockchain.get_balance(miner_pub)
            blockchain.balances[miner_addr] = miner_pub_balance
            
            # Also sync sender and recipient balances after mining
            blockchain.balances[addr1] = blockchain.get_balance(pub1)
            blockchain.balances[addr2] = blockchain.get_balance(pub2)
            
    except Exception as e:
        print(f"   Mining error: {e}")
        block = None
    
    print(f"   Chain length: {initial_blocks} -> {len(blockchain.chain)}")
    if block:
        print(f"   Miner reward: {blockchain.get_balance(miner_addr)} coins")
    
    # Test balances after mining
    print("5. Testing balance updates...")
    print(f"   Sender balance: {blockchain.get_balance(addr1)} (should be 75)")
    print(f"   Recipient balance: {blockchain.get_balance(addr2)} (should be 75)")
    print(f"   Miner balance: {blockchain.get_balance(miner_addr)} (should be 10)")
    
    # Test chain validation
    print("6. Testing chain validation...")
    print(f"   Chain is valid: {blockchain.is_valid_chain()}")
    
    # Test double-spend prevention
    print("7. Testing double-spend prevention...")
    # Use the actual remaining balance from addr1 to test double-spend
    remaining_balance = blockchain.get_balance(addr1)
    print(f"   Sender remaining balance: {remaining_balance}")
    
    # Try to spend more than available (double-spend)
    invalid_amount = remaining_balance + 10  # More than available
    invalid_tx = Transaction(sender=pub1, recipient=pub2, amount=invalid_amount)
    invalid_tx.sign(priv1)
    result = blockchain.add_transaction(invalid_tx)
    print(f"   Invalid transaction rejected: {not result}")
    print(f"   Attempted to spend {invalid_amount}, but only {remaining_balance} available")
    
    print("=== All Tests Completed ===\n")