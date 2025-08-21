## P2P Usage and Testing Guide

This guide walks you through launching multiple nodes, broadcasting transactions and blocks, verifying synchronization, testing double-spend prevention, and demonstrating blockchain immutability checks.

**📹 Video Demonstrations:**
- [Steps 1-5: Multi-node Setup & Broadcasting](https://www.loom.com/share/71fac1c63c994f3d912ca26ba12b884c?sid=4e2c113b-af30-4751-8e95-dc9c450f581d)
- [Steps 6-7: Immutability Testing & Double-Spend Prevention](https://www.loom.com/share/4af70355e0504448953dfb6a31b41e5f?sid=8189c3c2-a1fb-456a-8aa8-3fc28cb8e9e4)


### Step 1: Prepare Terminals
Open three terminals and cd into the project directory in each:
```bash
cd Blockchain_Simulation_A2
```

### Step 2: Launch a 3-Node Network
- Terminal 1 (Node 1):
```bash
python3 main.py 5000
```
- Terminal 2 (Node 2):
```bash
python3 main.py 5001 5000
```
- Terminal 3 (Node 3):
```bash
python3 main.py 5002 5000 5001
```
You should see startup logs in each terminal. Nodes will connect to listed peers and start background P2P services.

### Step 3: Broadcast a Transaction
Perform these actions in Terminal 1 (Node 1):
1) Create two wallets (Option 1 twice). Note their addresses; call them Wallet A and Wallet B.
2) Create a transaction (Option 2): send 25 coins from Wallet A to Wallet B.
   - When prompted for recipient, paste the 64-hex address for Wallet B.
3) You should see messages that the transaction was added and broadcast.

Check Terminal 2 and Terminal 3 for logs indicating the new transaction was received and added to their pending pools.

### Step 4: Broadcast a Block (Mining)
Still in Terminal 1 (Node 1):
1) Mine a block (Option 3). Select a miner wallet when prompted.
2) You should see the block mined and broadcast.

Check Terminal 2 and Terminal 3 for logs showing the new block was received and appended. On each node, use Option 4 (View node) to inspect blocks and transactions.
3) Do step 3 again with create transaction, then try to use Terminal 2 for mining a block
### Step 5: Verify Chain Synchronization
1) On Node 1, create another small transaction and mine another block (Options 2 then 3). Do the same on Node 2 if desired.
2) Node 3 will sync automatically. This can happen in two ways:
   - Periodic sync (~every 60 seconds), or
   - Immediately when Node 3 receives a transaction or a future block (which triggers a sync).
3) To force an immediate sync, from Node 1 create/broadcast any transaction; Node 3 will receive it and run sync before processing.
4) Use Option 4 on all nodes to confirm the same chain height and hashes.

Note: There is no manual "sync now" menu option; synchronization is automatic and event-driven.

### Step 6: Test Double-Spend Prevention
Goal: Attempt two spends from the same wallet that together exceed its balance before any mining occurs.

In Terminal 1 (Node 1):
1) Create two wallets if you haven’t already (Option 1 twice). By default, each new wallet starts with 100 coins.
2) Create Transaction 1 (Option 2): from Wallet A send 80 coins to Wallet B.
3) Without mining, immediately create Transaction 2 (Option 2): from the same Wallet A send 30 coins to Wallet B (or any recipient).

Expected outcome:
- Transaction 1 is accepted into the pending pool.
- Transaction 2 fails with a validation message (double-spend detected in pending pool) because 80 + 30 > 100 before mining adjusts balances.

You can then mine (Option 3) to confirm only valid transactions are included in a block.

Tip: The double-spend detection considers total pending outgoing amount from the sender vs. available balance, so any pair of pending transactions that exceed the balance should trigger rejection of the latter.

### Step 7: Demonstrate Immutability (Tamper Detection and Recovery)
This shows that tampering with stored blocks breaks validation and that nodes converge back to a valid longest chain.

Setup:
- Ensure Node 1 and Node 2 have mined at least 2-3 blocks so they share a healthy, valid chain.

Tamper a node's local storage:
1) Stop Node 2 (Ctrl+C in Terminal 2) so it won't rewrite state while you edit.
2) Open `blockchain.json` in a text editor and change a field inside a mined block (for example, modify a transaction amount or the `previous_hash`). Save the file.
3) Restart Node 2:
```bash
python3 main.py 5001 5000
```
4) In Node 2, run Option 8 (Run tests). Expected: it reports the blockchain is invalid.

Recover to the valid network chain:
5) On Node 1, mine one additional block so its chain becomes strictly longer than Node 2's.
6) Trigger Node 2 to sync:
   - Either wait up to 60 seconds for the periodic sync, or
   - From Node 1, create/broadcast any transaction; when Node 2 receives it, it will run synchronization first.
7) On Node 2, use Option 4 (View node) to confirm it now matches the longer, valid chain from its peers.

Why this works:
- Each block's hash commits to all critical fields. Manual edits cause hash mismatches, which validation detects.
- Nodes adopt the longest valid chain observed from peers, overwriting invalid local state once a strictly longer valid chain is seen.

### Troubleshooting
- If ports 5000–5002 are in use, choose different ports consistently across terminals.
- If you don’t see broadcast logs on peers, verify the startup arguments include peer ports and that no firewall is blocking localhost traffic.
- Synchronization is periodic; to accelerate, broadcast a transaction from a healthy node so peers immediately run sync before processing.
- All nodes read/write `blockchain.json` in the current working directory. When running multiple nodes from the same folder, they share this file; for clean isolation, run each node from a separate directory copy if needed.


