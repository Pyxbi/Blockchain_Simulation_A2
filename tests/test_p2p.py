#!/usr/bin/env python3
"""
Test P2P functionality
"""
from blockchain import Blockchain
from transaction import Transaction
import time
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO)

def test_p2p():
    print("=== Testing P2P Functionality ===")
    
    try:
        # Create main blockchain
        bc = Blockchain()
        print(f"✓ Main blockchain created with {len(bc.chain)} blocks")
        
        # Create test nodes
        node1 = Blockchain()
        node2 = Blockchain()
        print("✓ Test nodes created")
        
        # Connect nodes in a network
        bc.nodes = [node1, node2]
        node1.nodes = [bc, node2]
        node2.nodes = [bc, node1]
        print("✓ Nodes connected in P2P network")
        
        # Start P2P processing
        bc.start_node()
        node1.start_node()
        node2.start_node()
        print("✓ P2P nodes started")
        
        # Create test wallets
        addr1, priv_key1, pub_key1 = bc.create_wallet(1000)
        addr2, priv_key2, pub_key2 = bc.create_wallet(0)
        print(f"✓ Created wallets: {addr1[:8]}... (balance: {bc.get_balance(addr1)}) and {addr2[:8]}... (balance: {bc.get_balance(addr2)})")
        
        # Sync wallets to other nodes
        for node in [node1, node2]:
            node.wallets[addr1] = priv_key1
            node.public_keys[addr1] = pub_key1
            node.wallets[addr2] = priv_key2
            node.public_keys[addr2] = pub_key2
            node.balances[addr1] = 1000
            node.balances[addr2] = 0
        
        # Create and broadcast transaction
        tx = Transaction(pub_key1, pub_key2, 50)
        tx.sign(priv_key1)
        print(f"✓ Created transaction: {pub_key1[:8]}... -> {pub_key2[:8]}... (50 coins)")
        
        # Broadcast transaction
        bc.broadcast_transaction(tx)
        print("✓ Transaction broadcasted to network")
        
        # Wait for P2P processing
        time.sleep(2)
        
        # Check results
        print("\n=== P2P Results ===")
        print(f"Main blockchain pending: {len(bc.pending_transactions)}")
        print(f"Node1 pending: {len(node1.pending_transactions)}")
        print(f"Node2 pending: {len(node2.pending_transactions)}")
        
        if len(node1.pending_transactions) > 0 and len(node2.pending_transactions) > 0:
            print("✅ P2P transaction broadcasting WORKS!")
        else:
            print("❌ P2P transaction broadcasting may have issues")
        
        # Test block broadcasting
        if bc.pending_transactions:
            print("\n=== Testing Block Broadcasting ===")
            block = bc.mine_block(addr1)
            if block:
                bc.broadcast_block(block)
                time.sleep(1)
                
                print(f"Main blockchain blocks: {len(bc.chain)}")
                print(f"Node1 blocks: {len(node1.chain)}")
                print(f"Node2 blocks: {len(node2.chain)}")
                
                if len(node1.chain) == len(bc.chain) and len(node2.chain) == len(bc.chain):
                    print("✅ P2P block broadcasting WORKS!")
                else:
                    print("❌ P2P block broadcasting may have issues")
        
        print("\n=== P2P Test Completed ===")
        
    except Exception as e:
        print(f"❌ P2P test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_p2p()
