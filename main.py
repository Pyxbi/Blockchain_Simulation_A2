import sys
import threading
import time
import logging
from blockchain import Blockchain
from transaction import Transaction

# Configure logging - reduce verbosity for better UX
# Change logging.WARNING to logging.INFO to see the P2P messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """Complete CLI interface for interacting with the node."""
    # --- 1. Get Node Config from Command Line ---
    if len(sys.argv) < 2:
        print("Usage: python main.py <port> [peer_port1] [peer_port2] ...")
        print("Example (first node): python main.py 5000")
        print("Example (second node, connects to first): python main.py 5001 5000")
        sys.exit(1)

    port = int(sys.argv[1])
    host = '127.0.0.1'
    peer_ports = sys.argv[2:]

    # --- 2. Initialize a Single Node ---
    print(f"🚀 Initializing node node on port {port}...")
    # This is our single node instance
    node = Blockchain(host=host, port=port)

    # --- 3. Start the Server in a Background Thread ---
    # This is crucial! It runs the network listener without blocking the CLI.
    server_thread = threading.Thread(target=node.run, daemon=True)
    server_thread.start()
    print(f" Node server running in background at http://{host}:{port}")

    # --- 4. Connect to Peers ---
    for peer_p in peer_ports:
        peer_url = f"http://{host}:{peer_p}"
        node.connect_to_peer(peer_url)
    
    # Give the server a moment to start and connect
    time.sleep(2)
    print(" node CLI is ready!")

    # --- 5. Run Your Existing CLI ---
    # The `node` variable is now `node`.

    while True:
        print("\n=== node CLI ===")
        print("1. Create wallet")
        print("2. Create transaction")
        print("3. Mine block")
        print("4. View node")
        print("5. Check balance")
        print("6. View all wallets")
        print("7. Add funds to wallet (for testing)")
        print("8. Run basic tests")
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
            print(f"\n New wallet created!")
            print(f"Address: {address}")
            print(f"Private key: {private_key_hex}")
            print(f"Public key: {public_key_hex}")
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
                sender_choice = input("Select sender wallet (number 1-{}): ".format(len(wallet_list))).strip()
                
                # Check if user entered a wallet address instead of number
                if len(sender_choice) == 64:  # Looks like a hex address
                    print("Tip: Please enter the wallet NUMBER (1, 2, 3...), not the address")
                    print("   Example: Enter '1' to select the first wallet")
                    continue
                
                sender_idx = int(sender_choice) - 1
                if 0 <= sender_idx < len(wallet_list):
                    sender_addr, sender_priv = wallet_list[sender_idx]
                    sender_pub = node.public_keys.get(sender_addr)
                else:
                    print(f" Invalid wallet number. Please enter a number between 1 and {len(wallet_list)}")
                    continue
            except ValueError:
                print(f" Invalid input. Please enter a number between 1 and {len(wallet_list)}")
                continue
                
            print(f"Sender: {sender_addr[:16]}... (Balance: {node.get_balance(sender_addr)})")
            
            # Select recipient
            print("\nChoose recipient:")
            other_wallets = [(addr, priv) for addr, priv in wallet_list if addr != sender_addr]
            for i, (addr, _) in enumerate(other_wallets, 1):
                balance = node.get_balance(addr)
                print(f"{i}. {addr[:16]}... (Balance: {balance} coins)")
            print(f"{len(other_wallets) + 1}. Enter external public key")
                
            try:
                recipient_choice = input(f"Select recipient (number 1-{len(other_wallets) + 1}): ").strip()
                
                # Check if user entered a wallet address instead of number
                if len(recipient_choice) == 64:  # Looks like a hex address or public key
                    print("Tip: Please enter the recipient NUMBER, or choose option {} to enter a custom public key".format(len(other_wallets) + 1))
                    print("   Example: Enter '1' to select the first wallet, or '{}' to enter custom key".format(len(other_wallets) + 1))
                    continue
                
                choice_num = int(recipient_choice)
                
                if 1 <= choice_num <= len(other_wallets):
                    recipient_addr = other_wallets[choice_num - 1][0]
                    recipient_pub = node.public_keys.get(recipient_addr)
                elif choice_num == len(other_wallets) + 1:
                    recipient_pub = input("Enter recipient public key (64 hex chars): ").strip()
                    if len(recipient_pub) != 64:
                        print(" Invalid public key format. Must be exactly 64 hexadecimal characters")
                        continue
                    recipient_addr = recipient_pub  # Fix: set recipient_addr for custom public key
                else:
                    print(f" Invalid choice. Please enter a number between 1 and {len(other_wallets) + 1}")
                    continue
            except ValueError:
                print(f" Invalid input. Please enter a number between 1 and {len(other_wallets) + 1}")
                continue
            
            # Get amount
            try:
                amount = float(input("Enter amount to send: "))
                if amount <= 0:
                    print(" Amount must be positive")
                    continue
            except ValueError:
                print(" Invalid amount")
                continue
                
            # Check balance
            current_balance = node.get_balance(sender_addr)
            if current_balance < amount:
                print(f" Insufficient balance. Available: {current_balance}, Required: {amount}")
                continue
            
            # IMPORTANT: Ensure balance is available for the public key (used in transactions)
            # This is a workaround for the balance tracking inconsistency
            if sender_pub not in node.balances:
                node.balances[sender_pub] = current_balance
            elif node.balances[sender_pub] < amount:
                node.balances[sender_pub] = current_balance
            
            # Create and sign transaction
            tx = Transaction(sender=sender_pub, recipient=recipient_pub, amount=amount)
            tx.sign(sender_priv)
            
            # Add to node
            if node.add_transaction(tx):
                # Update balances immediately to reflect pending transaction
                node.balances[sender_addr] = node.balances.get(sender_addr, 0) - amount
                node.balances[sender_pub] = node.balances.get(sender_pub, 0) - amount
                
                print(" Transaction added to pending pool!")
                print(f"Transaction hash: {tx.signature[:16]}...")
                print(f"New available balance: {node.get_balance(sender_addr)} coins")
                
                # Save the updated balances
                node.save_to_disk()
                
                # Broadcast to network
                node.broadcast_transaction(tx)
            else:
                print(" Transaction failed validation")

        elif choice == '3':
            # Mine block
            if not node.pending_transactions:
                print("❌ No pending transactions to mine")
                continue
                
            if not node.wallets:
                print("❌ No wallets available. Create a wallet first.")
                continue
                
            print(f"\n⛏️  Mine Block ({len(node.pending_transactions)} pending transactions)")
            
            # Show current mempool status
            print("\n📋 Current Mempool:")
            for i, tx in enumerate(node.pending_transactions, 1):
                print(f"   {i}. {tx.sender[:16]}... → {tx.recipient[:16]}... : {tx.amount} coins")
            
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
                    miner_pub = node.public_keys.get(miner_addr)  # Get the public key for mining reward
                else:
                    print("❌ Invalid wallet selection")
                    continue
            except ValueError:
                print("❌ Invalid input")
                continue
                
            print(f"Mining with difficulty {node.difficulty}...")
            print("⏳ This may take a while...")
            print("📝 Note: Exactly 1 transaction will be mined per block")
            
            start_time = time.time()
            block = node.mine_block(miner_pub)  # Pass public key, not address
            end_time = time.time()
            
            if block:
                # Count user transactions (excluding mining reward)
                user_transactions = [tx for tx in block.transactions if tx.sender != "COINBASE"]
                mining_reward_tx = [tx for tx in block.transactions if tx.sender == "COINBASE"]
                mining_reward = mining_reward_tx[0].amount if mining_reward_tx else 0
                
                print(f"✅ Block #{block.height} mined successfully!")
                print(f"⏱️  Mining time: {end_time - start_time:.2f} seconds")
                print(f"🔗 Block hash: {block.hash}")
                print(f"📦 Transactions mined: {len(user_transactions)}")
                print(f"📋 Remaining in mempool: {len(node.pending_transactions)}")
                print(f"💰 Mining reward: {mining_reward} coins")
                print(f"💼 Miner's new balance: {node.get_balance(miner_addr)} coins")
                
                # Save the updated balances
                node.save_to_disk()
                
                # Broadcast to network
                node.broadcast_block(block)
                
                # Give P2P nodes time to process the broadcast before showing menu
                time.sleep(0.5)
            else:
                print("❌ Mining failed")

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
                print(" No wallets available. Create a wallet first.")
                continue
                
            print("\nBalance Checker")
            print("\nAvailable wallets:")
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
                    confirmed_balance = node.balances.get(address, 0)
                    
                    print(f"\nWallet Details:")
                    print(f"Address: {address}")
                    print(f"Confirmed Balance: {confirmed_balance} coins")
                    print(f"Available Balance: {balance} coins")
                    
                    if balance != confirmed_balance:
                        print(f"Pending: {confirmed_balance - balance} coins")
                else:
                    print(" Invalid wallet selection")
            except ValueError:
                print(" Invalid input")

        elif choice == '6':
            # View all wallets
            if not node.wallets:
                print(" No wallets available.")
                continue
                
            print(f"\nAll Wallets ({len(node.wallets)} total)")
            print("=" * 80)
            
            for i, (addr, priv_key) in enumerate(node.wallets.items(), 1):
                balance = node.get_balance(addr)
                confirmed_balance = node.balances.get(addr, 0)
                pub_key = node.public_keys.get(addr, "Unknown")
                
                print(f"\nWallet #{i}")
                print(f"   Address: {addr}")
                print(f"   Public Key: {pub_key}")
                print(f"   Private Key: {priv_key}")
                print(f"   Confirmed Balance: {confirmed_balance} coins")
                print(f"   Available Balance: {balance} coins")
                print("-" * 80)

        elif choice == '7':
            # Add funds (testing)
            print("\nAdd Test Funds")
            
            if node.wallets:
                print("\nAvailable wallets:")
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
                        print(" Invalid wallet selection")
                        continue
                except ValueError:
                    print(" Invalid input")
                    continue
            else:
                address = input("Enter wallet address to fund: ").strip()
                if len(address) != 64:
                    print(" Invalid address format")
                    continue
            
            try:
                amount = float(input("Enter amount to add: "))
                if amount <= 0:
                    print(" Amount must be positive")
                    continue
            except ValueError:
                print(" Invalid amount")
                continue
                
            # Add funds
            old_balance = node.balances.get(address, 0)
            node.balances[address] = old_balance + amount
            
            # Also add to public key if this is a known wallet
            pub_key = node.public_keys.get(address)
            if pub_key:
                node.balances[pub_key] = node.balances.get(pub_key, 0) + amount
            
            node.save_to_disk()
            
            print(f" Added {amount} coins to {address[:16]}...")
            print(f"New balance: {node.get_balance(address)} coins")

        elif choice == '8':
            # for testing demo of Immutability in section 2 in report
            is_valid_chain, message = node.is_valid_chain()
            if is_valid_chain:
                print("Blockchain is valid!")
            else:
               print("Blockchain is invalid:", message)
            print("\nRunning basic tests...")

        elif choice == '9':
            print(f"\n📡 Connected Peers: {list(node.peers) if node.peers else 'None'}")

        elif choice == '10':
            print("\nManually triggering chain synchronization...")
            node.sync_chain()

        else:
            print(" Invalid choice. Please enter a number between 1-9.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting gracefully...")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        logging.error(f"Unexpected error in main: {e}", exc_info=True)