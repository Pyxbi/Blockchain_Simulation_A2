import sys
import threading
import time
import logging
from blockchain import Blockchain
from transaction import Transaction
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey

# Configure logging for seeing the P2P messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """Complete CLI interface for interacting with the node."""
    # get Node Config from Command Line
    if len(sys.argv) < 2:
        print("Usage: python main.py <port> [peer_port1] [peer_port2] ...")
        print("Example (first node): python main.py 5000")
        print("Example (second node, connects to first): python main.py 5001 5000")
        sys.exit(1)

    port = int(sys.argv[1])
    host = '127.0.0.1'
    peer_ports = sys.argv[2:]

   # initialization single node
    print(f" Initializing node node on port {port}...")
    # This is our single node instance
    node = Blockchain(host=host, port=port)

    # start the server in a background thread
    # This is crucial because it runs the network listener without blocking the CLI.
    server_thread = threading.Thread(target=node.run, daemon=True)
    server_thread.start()
    print(f" Node server running in background at http://{host}:{port}")

    # connect to any specified peer nodes
    for peer_p in peer_ports:
        peer_url = f"http://{host}:{peer_p}"
        node.connect_to_peer(peer_url)
    
    # Give the server a moment to start and connect
    time.sleep(2)
    print(" node CLI is ready!")

    # run CLI
    # The `node` variable is now `node`.

    while True:
        print("\n=== BLOCKCHAIN SIMULATION CLI ===")
        print("1. Create wallet")
        print("2. Create transaction")
        print("3. Mine block")
        print("4. View node")
        print("5. Check balance")
        print("6. View all wallets")
        print("7. Faucet (add test funds)")
        print("8. Validate blockchain test")
        print("9. Exit")
        
        try:
            choice = input(f"Node@{port}> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break

        if choice == '1':
            # Create wallet
            try:
                initial_balance = input("Enter initial balance (default 100): ").strip()
                balance = float(initial_balance) if initial_balance else 100.0
            except ValueError:
                balance = 100.0
                
            address, private_key_hex, public_key_hex = node.create_wallet(initial_balance=balance)
            print(f"\nNew wallet created!")
            print(f"Address: {address}")
            print(f"Private Key: {private_key_hex}")
            print(f"Public Key: {public_key_hex}")
            print(f"Initial balance: {node.get_balance(address)} coins")

        elif choice == '2':
            # Create transaction
            if not node.wallets:
                print("No wallets available. Create a wallet first.")
                continue
                
            print("\nCreate Transaction")
            print("\nAvailable wallets:")
            wallet_list = list(node.wallets.items())
            for i, (addr, _) in enumerate(wallet_list, 1):
                balance = node.get_balance(addr)
                print(f"{i}. {addr[:16]}... (Balance: {balance} coins)")
            
            # Select sender
            try:
                sender_choice = input(f"Select sender wallet (1-{len(wallet_list)}): ").strip()
                sender_idx = int(sender_choice) - 1
                if 0 <= sender_idx < len(wallet_list):
                    sender_addr, sender_priv_hex = wallet_list[sender_idx]
                    sender_priv = SigningKey(sender_priv_hex, encoder=HexEncoder)
                    sender_pub = node.public_keys.get(sender_addr)
                else:
                    print(f"Invalid wallet number. Please enter 1-{len(wallet_list)}")
                    continue
            except ValueError:
                print("Invalid input. Please enter a number.")
                continue
                
            print(f"Sender: {sender_addr[:16]}... (Balance: {node.get_balance(sender_addr)} coins)")
            
            # Get recipient address
            recipient_addr = input("\nEnter recipient address (64 hex characters): ").strip()
            if len(recipient_addr) != 64:
                print("Invalid address format. Must be exactly 64 hexadecimal characters.")
                continue
            
            # For transactions, recipient should be the public key, not address
            # Check if this is one of our wallets (then use public key), otherwise use the address as-is
            recipient_pub = node.public_keys.get(recipient_addr, recipient_addr)
            
            # Get amount
            try:
                amount = float(input("Enter amount to send: "))
                if amount <= 0:
                    print("Amount must be positive")
                    continue
            except ValueError:
                print("Invalid amount")
                continue
            
            # Create and sign transaction
            tx = Transaction(sender=sender_pub, recipient=recipient_pub, amount=amount)
            tx.sign(sender_priv)
            
            # Add to node
            if node.add_transaction(tx):
                print("Transaction added to pending pool!")
                print(f"Transaction hash: {tx.signature[:16]}...")
                print(f"From: {sender_addr[:16]}...")
                print(f"To: {recipient_addr[:16]}...")
                print(f"Amount: {amount} coins")
                
                # Broadcast to network
                node.broadcast_transaction(tx)
            else:
                print("Transaction failed validation")


        elif choice == '3':
            # Mine block
            if not node.pending_transactions:
                print("No pending transactions to mine")
                continue
                
            if not node.wallets:
                print("No wallets available. Create a wallet first.")
                continue
                
            print(f"\n Mining Block ({len(node.pending_transactions)} pending transactions)")
            
            # Show current mempool
            for i, tx in enumerate(node.pending_transactions, 1):
                print(f"   {i}. {tx.sender[:16]}... → {tx.recipient[:16]}... : {tx.amount} coins")
            
            # Select miner wallet
            print("\nSelect miner wallet:")
            wallet_list = list(node.wallets.items())
            for i, (addr, _) in enumerate(wallet_list, 1):
                balance = node.get_balance(addr)
                print(f"{i}. {addr[:16]}... (Balance: {balance} coins)")
                
            try:
                miner_choice = input("Select miner wallet (number): ").strip()
                miner_idx = int(miner_choice) - 1
                if 0 <= miner_idx < len(wallet_list):
                    miner_addr, _ = wallet_list[miner_idx]
                    miner_pub = node.public_keys.get(miner_addr)
                else:
                    print("Invalid wallet selection")
                    continue
            except ValueError:
                print("Invalid input")
                continue
                
            print(f" Mining with difficulty {node.difficulty}...")
            
            start_time = time.time()
            block = node.mine_block(miner_pub)
            end_time = time.time()
            
            if block:
                user_transactions = [tx for tx in block.transactions if tx.sender != "COINBASE"]
                mining_reward_tx = [tx for tx in block.transactions if tx.sender == "COINBASE"]
                mining_reward = mining_reward_tx[0].amount if mining_reward_tx else 0
                
                print(f"Block #{block.height} mined successfully!")
                print(f"  Time: {end_time - start_time:.2f}s")
                print(f" Hash: {block.hash[:16]}...")
                print(f" Mining reward: {mining_reward} coins")
                print(f" Remaining in mempool: {len(node.pending_transactions)}")
                
                node.broadcast_block(block)
            else:
                print("Mining failed")

        elif choice == '4':
            # View node
            print(f"\nNode Explorer ({len(node.chain)} blocks)")
            print("=" * 60)
            
            for block in node.chain:
                print(f"\nBlock #{block.height}")
                print(f"   Hash: {block.hash}")
                print(f"   Previous: {block.previous_hash}")
                print(f"   Timestamp: {time.ctime(block.timestamp)}")
                print(f"   Difficulty: {block.difficulty}")
                print(f"   Nonce: {block.nonce}")
                print(f"   Mined by: {block.mined_by[:16] if len(block.mined_by) > 16 else block.mined_by}...")
                print(f"   Merkle root: {block.merkle_root}")
                
                if block.transactions:
                    print(f"   Transactions ({len(block.transactions)}):")
                    for i, tx in enumerate(block.transactions, 1):
                        if hasattr(tx, 'sender') and tx.sender == "COINBASE":
                            print(f"     {i}.COINBASE → {tx.recipient[:16]}... : {tx.amount} coins (reward)")
                        else:
                            print(f"     {i}. {tx.sender[:16]}... → {tx.recipient[:16]}... : {tx.amount} coins")
                else:
                    print("   Transactions: None (Genesis block)")
                print("-" * 60)

        elif choice == '5':
            # Check balance
            if not node.wallets:
                print("No wallets available. Create a wallet first.")
                continue
                
            print("\nBalance Checker")
            wallet_list = list(node.wallets.keys())
            for i, addr in enumerate(wallet_list, 1):
                balance = node.get_balance(addr)
                print(f"{i}. {addr[:16]}... : {balance} coins")
            
            try:
                wallet_choice = input("Select wallet to check (number): ").strip()
                wallet_idx = int(wallet_choice) - 1
                if 0 <= wallet_idx < len(wallet_list):
                    address = wallet_list[wallet_idx]
                    balance = node.get_balance(address)
                    
                    print(f"\n Wallet Details:")
                    print(f"Address: {address}")
                    print(f"Balance: {balance} coins")
                else:
                    print("Invalid wallet selection")
            except ValueError:
                print("Invalid input")

        elif choice == '6':
            # View all wallets
            if not node.wallets:
                print("No wallets available.")
                continue
                
            print(f"\n All Wallets ({len(node.wallets)} total)")
            print("=" * 70)
            
            for i, (addr, priv_key) in enumerate(node.wallets.items(), 1):
                balance = node.get_balance(addr)
                pub_key = node.public_keys.get(addr, "Unknown")
                
                print(f"\nWallet #{i}")
                print(f"   Address: {addr}")
                print(f"   Balance: {balance} coins")
                print(f"   Public Key: {pub_key}")
                print("-" * 70)
            

        elif choice == '7':
            # Add funds (testing)
            print("\n Add Test Funds")
            
            if not node.wallets:
                print("No wallets available. Create a wallet first.")
                continue
                
            wallet_list = list(node.wallets.keys())
            for i, addr in enumerate(wallet_list, 1):
                balance = node.get_balance(addr)
                print(f"{i}. {addr[:16]}... : {balance} coins")
            
            try:
                wallet_choice = input("Select wallet to fund (number): ").strip()
                wallet_idx = int(wallet_choice) - 1
                if 0 <= wallet_idx < len(wallet_list):
                    address = wallet_list[wallet_idx]
                else:
                    print("Invalid wallet selection")
                    continue
                    
                amount = float(input("Enter amount to add: "))
                if amount <= 0:
                    print("Amount must be positive")
                    continue
            except (ValueError, IndexError):
                print("Invalid input")
                continue
                
            # Add funds
            old_balance = node.balances.get(address, 0)
            node.balances[address] = old_balance + amount
            node.save_to_disk()
            
            print(f"Added {amount} coins to {address[:16]}...")
            print(f"New balance: {node.get_balance(address)} coins")

        elif choice == '8':
            # Basic tests
            is_valid_chain, message = node.is_valid_chain()
            if is_valid_chain:
                print("Blockchain is valid!")
            else:
                print(f"Blockchain is invalid: {message}")

        elif choice == '9':
            print(" Exiting...")
            break

        else:
            print("Invalid choice. Please enter 1-9.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting gracefully...")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        logging.error(f"Unexpected error in main: {e}", exc_info=True)