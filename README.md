# Blockchain Simulation Assignment

## Overview
This project is a comprehensive, modular blockchain implementation in Python, designed to meet academic requirements for a blockchain assignment. It features a robust block structure, Ed25519 cryptographic signing, transaction management, Proof-of-Work consensus, double-spend prevention, P2P networking, wallet functionality, data persistence, and an interactive command-line interface.

## Features

### Core Blockchain Components
- **Block Structure**: Complete block implementation with index, timestamp, transactions, previous hash, nonce, hash, difficulty, and miner information
- **Cryptographic Security**: Ed25519 digital signatures using PyNaCl for transaction authentication
- **Chain Integrity**: SHA-256 hash linking and comprehensive chain validation
- **Transaction Pool**: Pending transaction management with double-spend prevention (account model)
- **Proof-of-Work Consensus**: Adjustable difficulty mining with automatic difficulty adjustment
- **Mining Rewards**: Automatic coinbase transactions for miners
- **Balance Tracking**: Real-time balance management with sender/recipient synchronization

### Advanced Features
- **Wallet Functionality**: Complete wallet creation with public/private key pairs
- **Data Persistence**: JSON-based blockchain state storage and recovery
- **Schema Validation**: Marshmallow-based transaction and block validation
- **P2P Networking**: Multi-node blockchain synchronization and transaction broadcasting
- **Double-Spend Prevention**: Comprehensive balance checking including pending transactions
- **Global Ordering**: Height-based block ordering with proper chain validation

### User Interface
- **Interactive CLI**: Menu-driven interface with 9 comprehensive options
- **Wallet Management**: Create wallets, view all wallets, add test funds
- **Transaction Management**: Create and broadcast transactions with signature verification
- **Mining Interface**: Mine blocks with automatic reward distribution
- **Blockchain Viewing**: Display complete blockchain with transaction details
- **Balance Checking**: Real-time balance queries for any address
- **Testing Suite**: Built-in comprehensive test function for all features

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd blockchain-demo-A2
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the interactive CLI:**
   ```bash
   python main.py
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
1. **Create wallets** (Option 1) - Generate Ed25519 key pairs for users
2. **Add test funds** (Option 7) - Add initial balance for testing
3. **Create transactions** (Option 2) - Send funds between wallets with digital signatures
4. **Mine blocks** (Option 3) - Process pending transactions and earn mining rewards
5. **View blockchain** (Option 4) - Inspect the complete chain with all transactions
6. **Check balances** (Option 5) - Verify account balances after transactions
7. **Run tests** (Option 8) - Execute comprehensive test suite

## Architecture

### File Structure
- `main.py` - Interactive CLI interface and user interaction logic
- `blockchain.py` - Core blockchain class with persistence and P2P capabilities
- `models.py` - Block and data structure definitions
- `transaction.py` - Transaction class with Ed25519 signature verification
- `consensus.py` - Proof-of-Work implementation with difficulty adjustment
- `wallet.py` - Wallet creation and key management
- `schema.py` - Marshmallow validation schemas for transactions and blocks
- `persistence.py` - JSON-based data storage and recovery
- `p2p.py` - Multi-node networking and synchronization
- `tests/` - Test files for various components

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

## Testing

The application includes a comprehensive testing suite (Option 8 in CLI) that validates:
- Wallet creation and key generation
- Transaction signing and verification
- Mining and reward distribution
- Balance tracking and updates
- Chain validation and integrity
- Double-spend prevention
- P2P synchronization

You can also run individual test files:
```bash
python tests/test_mining.py
python tests/test_function.py
```

## Extending the System

### Potential Enhancements
- **Database Storage**: Replace JSON with SQLite or PostgreSQL
- **REST API**: Add HTTP endpoints for external integration
- **Real P2P Network**: Implement actual network communication
- **Smart Contracts**: Add programmable transaction logic
- **Web Interface**: Build a web-based dashboard
- **Performance Optimization**: Add caching and indexing
- **Advanced Consensus**: Implement Proof-of-Stake or other algorithms

### Development Notes
- All external dependencies are minimal and well-documented
- Code follows Python best practices with comprehensive error handling
- Modular design allows easy extension and modification
- Extensive logging for debugging and monitoring

## Academic Requirements Compliance

This implementation satisfies all 10 core blockchain requirements:
1. ✅ **Block Structure** - Complete block implementation with all required fields
2. ✅ **Cryptographic Hashing** - SHA-256 for blocks, Ed25519 for transactions
3. ✅ **Transaction Handling** - Full transaction lifecycle with digital signatures
4. ✅ **Consensus Mechanism** - Proof-of-Work with dynamic difficulty adjustment
5. ✅ **Double-Spend Prevention** - Comprehensive balance and pending transaction validation
6. ✅ **Global Ordering** - Height-based block ordering with chain validation
7. ✅ **Data Persistence** - JSON-based storage with automatic save/load
8. ✅ **User Interface** - Interactive CLI with comprehensive menu options
9. ✅ **P2P Networking** - Multi-node synchronization and transaction broadcasting
10. ✅ **Wallet Functionality** - Complete Ed25519 key pair management and signing

## Author
- Your Name Here # Blockchain_Simulation_A2
