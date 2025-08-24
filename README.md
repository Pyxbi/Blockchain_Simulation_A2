# Blockchain Simulation Assignment

## Overview
This project is a comprehensive, modular blockchain implementation in Python, designed to meet academic requirements for a blockchain assignment. It features a robust block structure, Ed25519 cryptographic signing, transaction management, Proof-of-Work consensus, double-spend prevention, P2P networking, wallet functionality, data persistence, and an interactive command-line interface.


## Blockchain Structure

- `main.py`: Acts as the command-line interface (CLI) controller, handling user interactions and orchestrating operations across other modules. It initializes the blockchain node, manages peer connections, and provides a user-friendly interface for actions like creating wallets, sending transactions, mining blocks, and viewing the blockchain state.

- `blockchain.py`: The core module that encapsulates the blockchain's primary logic, including chain management, transaction validation, block mining, and balance tracking. It inherits from `P2PNode` and `Persistence` to integrate peer-to-peer (P2P) networking and disk persistence.

- `consensus.py`: Implements the proof-of-work (PoW) consensus mechanism and difficulty adjustment logic, ensuring the security and integrity of the blockchain.

- `wallet.py`: Manages cryptographic key pair generation and wallet address creation using the Ed25519 algorithm.

- `transaction.py`: Defines the `Transaction` class, handling transaction creation, signing, and verification.

- `models.py`: Contains data models (`Block` and `Peer`) with methods for serialization, deserialization, and hash calculations.

- `p2p.py`: Manages P2P networking, including peer discovery, transaction and block broadcasting, and chain synchronization.

- `persistence.py`: Handles saving and loading the blockchain state to/from disk in JSON format.

- `schema.py`: Defines schemas for validating transaction and block data using the Marshmallow library.

## Features


### User Interface
- **Interactive CLI**: Menu-driven interface with 9 comprehensive options
- **Wallet Management**: Create wallets, view all wallets, add test funds
- **Transaction Management**: Create and broadcast transactions with signature verification
- **Mining Interface**: Mine blocks with automatic reward distribution
- **Blockchain Viewing**: Display complete blockchain with transaction details
- **Balance Checking**: Real-time balance queries for any address


## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Blockchain_Simulation_A2
   ```

2. **(Recommended) Create a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the interactive CLI:**
   ```bash
   python3 main.py 5000 (for node 1)
   python3 main.py 5001 5000 (for node 2)
   python3 main.py 5002 5001 5000 (for node 3)
   and so on...
   ```

## Usage

The application provides an interactive menu-driven interface:

```
=== Blockchain CLI ===
1. Create wallet
2. Create transaction
3. Mine block
4. View blockchain
5. Check balance
6. View all wallets
7. Add funds to wallet (for testing)
8. Run basic tests
9. Exit
```

### Example Workflow:

For a full step-by-step walkthrough of multi-node setup, broadcasting, synchronization, double-spend prevention, and immutability checks, see:
[GUIDE_P2P_Usage_and_Testing.md](./GUIDE_P2P_Usage_and_Testing.md)

### Key Design Decisions
- **Ed25519 Cryptography**: Used PyNaCl for fast, secure digital signatures
- **Account Model**: Balance tracking instead of UTXO for simplicity
- **JSON Persistence**: Human-readable storage format for easy debugging
- **Modular Design**: Separate concerns with inheritance for clean architecture
- **Comprehensive Validation**: Schema validation for all data structures
- **Real-time Synchronization**: Automatic balance updates and chain validation

## Security Features

- **Digital Signatures**: All transactions signed with Ed25519 private keys
- **Hash Chain Integrity**: Each block cryptographically linked to previous block
- **Double-Spend Prevention**: Balance verification before transaction acceptance
- **Proof-of-Work**: Computational proof required for block acceptance
- **Chain Validation**: Complete chain integrity checks on synchronization
- **Schema Validation**: Input validation for all transactions and blocks


Note: Tests are integrated into the CLI (Option 8). There is no separate test directory in this repository; use the built-in tests to validate core functionality.




