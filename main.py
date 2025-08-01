from blockchain import Blockchain
from tests.test_function import TestBlockchain
from transaction import Transaction
import time
import logging

# Configure logging - reduce verbosity for better UX
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """Complete CLI interface for interacting with the blockchain."""
    print("🚀 Welcome to the Blockchain Demo!")
    print("Initializing blockchain...")
    
    blockchain = Blockchain()
    runtest = TestBlockchain()
    
    # Create test nodes for P2P simulation
    print("Setting up P2P network simulation...")
    node1 = Blockchain()
    node2 = Blockchain()
    blockchain.nodes.extend([node1, node2])
    node1.nodes.extend([blockchain, node2])
    node2.nodes.extend([blockchain, node1])
    
    # Start P2P nodes
    blockchain.start_node()
    node1.start_node()
    node2.start_node()
    
    print("✅ Blockchain initialized successfully!")

    while True:
        print("\n=== Blockchain CLI ===")
        print("1. Create wallet")
        print("2. Create transaction")
        print("3. Mine block")
        print("4. View blockchain")
        print("5. Check balance")
        print("6. View all wallets")
        print("7. Add funds to wallet (for testing)")
        print("8. Run basic tests")
        print("9. Exit")
        
        try:
            choice = input("Enter choice (1-9): ").strip()
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
                
            address, private_key_hex, public_key_hex = blockchain.create_wallet(initial_balance=balance)
            print(f"\n✅ New wallet created!")
            print(f"Address: {address}")
            print(f"Private key: {private_key_hex}")
            print(f"Public key: {public_key_hex}")
            print(f"Initial balance: {blockchain.get_balance(address)} coins")

        elif choice == '2':
            # Create transaction
            if not blockchain.wallets:
                print("❌ No wallets available. Create a wallet first.")
                continue
                
            print("\n📤 Create Transaction")
            print("\nAvailable wallets:")
            wallet_list = list(blockchain.wallets.items())
            for i, (addr, _) in enumerate(wallet_list, 1):
                balance = blockchain.get_balance(addr)
                print(f"{i}. {addr[:16]}... (Balance: {balance} coins)")
            
            # Select sender
            try:
                sender_choice = input("Select sender wallet (number 1-{}): ".format(len(wallet_list))).strip()
                
                # Check if user entered a wallet address instead of number
                if len(sender_choice) == 64:  # Looks like a hex address
                    print("💡 Tip: Please enter the wallet NUMBER (1, 2, 3...), not the address")
                    print("   Example: Enter '1' to select the first wallet")
                    continue
                
                sender_idx = int(sender_choice) - 1
                if 0 <= sender_idx < len(wallet_list):
                    sender_addr, sender_priv = wallet_list[sender_idx]
                    sender_pub = blockchain.public_keys.get(sender_addr)
                else:
                    print(f"❌ Invalid wallet number. Please enter a number between 1 and {len(wallet_list)}")
                    continue
            except ValueError:
                print(f"❌ Invalid input. Please enter a number between 1 and {len(wallet_list)}")
                continue
                
            print(f"Sender: {sender_addr[:16]}... (Balance: {blockchain.get_balance(sender_addr)})")
            
            # Select recipient
            print("\nChoose recipient:")
            other_wallets = [(addr, priv) for addr, priv in wallet_list if addr != sender_addr]
            for i, (addr, _) in enumerate(other_wallets, 1):
                balance = blockchain.get_balance(addr)
                print(f"{i}. {addr[:16]}... (Balance: {balance} coins)")
            print(f"{len(other_wallets) + 1}. Enter external public key")
                
            try:
                recipient_choice = input(f"Select recipient (number 1-{len(other_wallets) + 1}): ").strip()
                
                # Check if user entered a wallet address instead of number
                if len(recipient_choice) == 64:  # Looks like a hex address or public key
                    print("💡 Tip: Please enter the recipient NUMBER, or choose option {} to enter a custom public key".format(len(other_wallets) + 1))
                    print("   Example: Enter '1' to select the first wallet, or '{}' to enter custom key".format(len(other_wallets) + 1))
                    continue
                
                choice_num = int(recipient_choice)
                
                if 1 <= choice_num <= len(other_wallets):
                    recipient_addr = other_wallets[choice_num - 1][0]
                    recipient_pub = blockchain.public_keys.get(recipient_addr)
                elif choice_num == len(other_wallets) + 1:
                    recipient_pub = input("Enter recipient public key (64 hex chars): ").strip()
                    if len(recipient_pub) != 64:
                        print("❌ Invalid public key format. Must be exactly 64 hexadecimal characters")
                        continue
                else:
                    print(f"❌ Invalid choice. Please enter a number between 1 and {len(other_wallets) + 1}")
                    continue
            except ValueError:
                print(f"❌ Invalid input. Please enter a number between 1 and {len(other_wallets) + 1}")
                continue
            
            # Get amount
            try:
                amount = float(input("Enter amount to send: "))
                if amount <= 0:
                    print("❌ Amount must be positive")
                    continue
            except ValueError:
                print("❌ Invalid amount")
                continue
                
            # Check balance
            current_balance = blockchain.get_balance(sender_addr)
            if current_balance < amount:
                print(f"❌ Insufficient balance. Available: {current_balance}, Required: {amount}")
                continue
            
            # IMPORTANT: Ensure balance is available for the public key (used in transactions)
            # This is a workaround for the balance tracking inconsistency
            if sender_pub not in blockchain.balances:
                blockchain.balances[sender_pub] = current_balance
            elif blockchain.balances[sender_pub] < amount:
                blockchain.balances[sender_pub] = current_balance
            
            # Create and sign transaction
            tx = Transaction(sender=sender_pub, recipient=recipient_pub, amount=amount)
            tx.sign(sender_priv)
            
            # Add to blockchain
            if blockchain.add_transaction(tx):
                # Update balances immediately to reflect pending transaction
                blockchain.balances[sender_addr] = blockchain.balances.get(sender_addr, 0) - amount
                blockchain.balances[sender_pub] = blockchain.balances.get(sender_pub, 0) - amount
                
                print("✅ Transaction added to pending pool!")
                print(f"Transaction hash: {tx.signature[:16]}...")
                print(f"New available balance: {blockchain.get_balance(sender_addr)} coins")
                
                # Save the updated balances
                blockchain.save_to_disk()
                
                # Ensure all P2P nodes have the updated balance before broadcasting
                for node in blockchain.nodes:
                    # Sync balances to P2P nodes
                    if sender_addr in blockchain.balances:
                        node.balances[sender_addr] = blockchain.balances[sender_addr]
                    if sender_pub in blockchain.balances:
                        node.balances[sender_pub] = blockchain.balances[sender_pub]
                
                # Broadcast to network
                blockchain.broadcast_transaction(tx)
            else:
                print("❌ Transaction failed validation")

        elif choice == '3':
            # Mine block
            if not blockchain.pending_transactions:
                print("❌ No pending transactions to mine")
                continue
                
            if not blockchain.wallets:
                print("❌ No wallets available. Create a wallet first.")
                continue
                
            print(f"\n⛏️  Mine Block ({len(blockchain.pending_transactions)} pending transactions)")
            print("\nSelect miner wallet:")
            wallet_list = list(blockchain.wallets.items())
            for i, (addr, _) in enumerate(wallet_list, 1):
                balance = blockchain.get_balance(addr)
                print(f"{i}. {addr[:16]}... (Balance: {balance} coins)")
                
            try:
                miner_choice = input("Select miner wallet (number): ").strip()
                miner_idx = int(miner_choice) - 1
                if 0 <= miner_idx < len(wallet_list):
                    miner_addr, _ = wallet_list[miner_idx]
                    miner_pub = blockchain.public_keys.get(miner_addr)
                else:
                    print("❌ Invalid wallet selection")
                    continue
            except ValueError:
                print("❌ Invalid input")
                continue
                
            print(f"Mining with difficulty {blockchain.difficulty}...")
            print("⏳ This may take a while...")
            
            start_time = time.time()
            block = blockchain.mine_block(miner_pub)
            end_time = time.time()
            
            if block:
                # Sync miner reward balance between public key and wallet address
                # Add the mining reward to the existing wallet balance instead of overwriting
                mining_reward = 10  # Standard mining reward
                current_miner_balance = blockchain.get_balance(miner_addr)
                new_miner_balance = current_miner_balance + mining_reward
                blockchain.balances[miner_addr] = new_miner_balance
                
                # Also ensure public key balance is consistent
                blockchain.balances[miner_pub] = blockchain.get_balance(miner_pub)
                
                print(f"✅ Block #{block.height} mined successfully!")
                print(f"⏱️  Mining time: {end_time - start_time:.2f} seconds")
                print(f"🔗 Block hash: {block.hash}")
                print(f"💰 Mining reward: {mining_reward} coins")
                print(f"💼 Miner's new balance: {blockchain.get_balance(miner_addr)} coins")
                
                # Save the updated balances
                blockchain.save_to_disk()
                
                # Broadcast to network
                blockchain.broadcast_block(block)
                
                # Give P2P nodes time to process the broadcast before showing menu
                time.sleep(0.5)
            else:
                print("❌ Mining failed")

        elif choice == '4':
            # View blockchain
            print(f"\n🔗 Blockchain Explorer ({len(blockchain.chain)} blocks)")
            print("=" * 60)
            
            for block in blockchain.chain:
                print(f"\n📦 Block #{block.height}")
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
                            print(f"     {i}. 💰 COINBASE → {tx.recipient[:16]}... : {tx.amount} coins (reward)")
                        else:
                            print(f"     {i}. 💸 {tx.sender[:16]}... → {tx.recipient[:16]}... : {tx.amount} coins")
                else:
                    print("   Transactions: None (Genesis block)")
                print("-" * 60)

        elif choice == '5':
            # Check balance
            if not blockchain.wallets:
                print("❌ No wallets available. Create a wallet first.")
                continue
                
            print("\n💰 Balance Checker")
            print("\nAvailable wallets:")
            wallet_list = list(blockchain.wallets.keys())
            for i, addr in enumerate(wallet_list, 1):
                balance = blockchain.get_balance(addr)
                print(f"{i}. {addr[:16]}... : {balance} coins")
            
            try:
                wallet_choice = input("Select wallet to check (number): ").strip()
                wallet_idx = int(wallet_choice) - 1
                if 0 <= wallet_idx < len(wallet_list):
                    address = wallet_list[wallet_idx]
                    balance = blockchain.get_balance(address)
                    confirmed_balance = blockchain.balances.get(address, 0)
                    
                    print(f"\n📊 Wallet Details:")
                    print(f"Address: {address}")
                    print(f"Confirmed Balance: {confirmed_balance} coins")
                    print(f"Available Balance: {balance} coins")
                    
                    if balance != confirmed_balance:
                        print(f"⏳ Pending: {confirmed_balance - balance} coins")
                else:
                    print("❌ Invalid wallet selection")
            except ValueError:
                print("❌ Invalid input")

        elif choice == '6':
            # View all wallets
            if not blockchain.wallets:
                print("❌ No wallets available.")
                continue
                
            print(f"\n👛 All Wallets ({len(blockchain.wallets)} total)")
            print("=" * 80)
            
            for i, (addr, priv_key) in enumerate(blockchain.wallets.items(), 1):
                balance = blockchain.get_balance(addr)
                confirmed_balance = blockchain.balances.get(addr, 0)
                pub_key = blockchain.public_keys.get(addr, "Unknown")
                
                print(f"\n🏦 Wallet #{i}")
                print(f"   Address: {addr}")
                print(f"   Public Key: {pub_key}")
                print(f"   Private Key: {priv_key}")
                print(f"   Confirmed Balance: {confirmed_balance} coins")
                print(f"   Available Balance: {balance} coins")
                print("-" * 80)

        elif choice == '7':
            # Add funds (testing)
            print("\n💵 Add Test Funds")
            
            if blockchain.wallets:
                print("\nAvailable wallets:")
                wallet_list = list(blockchain.wallets.keys())
                for i, addr in enumerate(wallet_list, 1):
                    balance = blockchain.get_balance(addr)
                    print(f"{i}. {addr[:16]}... : {balance} coins")
                
                try:
                    wallet_choice = input("Select wallet to fund (number): ").strip()
                    wallet_idx = int(wallet_choice) - 1
                    if 0 <= wallet_idx < len(wallet_list):
                        address = wallet_list[wallet_idx]
                    else:
                        print("❌ Invalid wallet selection")
                        continue
                except ValueError:
                    print("❌ Invalid input")
                    continue
            else:
                address = input("Enter wallet address to fund: ").strip()
                if len(address) != 64:
                    print("❌ Invalid address format")
                    continue
            
            try:
                amount = float(input("Enter amount to add: "))
                if amount <= 0:
                    print("❌ Amount must be positive")
                    continue
            except ValueError:
                print("❌ Invalid amount")
                continue
                
            # Add funds
            old_balance = blockchain.balances.get(address, 0)
            blockchain.balances[address] = old_balance + amount
            
            # Also add to public key if this is a known wallet
            pub_key = blockchain.public_keys.get(address)
            if pub_key:
                blockchain.balances[pub_key] = blockchain.balances.get(pub_key, 0) + amount
            
            blockchain.save_to_disk()
            
            print(f"✅ Added {amount} coins to {address[:16]}...")
            print(f"💰 New balance: {blockchain.get_balance(address)} coins")

        elif choice == '8':
            # Run tests
            runtest.run_tests()

        elif choice == '9':
            # Exit
            print("💾 Saving blockchain state...")
            blockchain.save_to_disk()
            print("👋 Thank you for using the Blockchain Demo!")
            print("💫 Blockchain saved successfully. Goodbye!")
            break

        else:
            print("❌ Invalid choice. Please enter a number between 1-9.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user. Exiting gracefully...")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        logging.error(f"Unexpected error in main: {e}", exc_info=True)