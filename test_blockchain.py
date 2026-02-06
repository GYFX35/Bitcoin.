import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'stubs')))

import pytest
import json
import os
import binascii
from ecdsa import SigningKey, SECP256k1
from blockchain import Blockchain

@pytest.fixture
def blockchain():
    # Use a different port for testing to avoid overwriting real blockchain files
    bc = Blockchain(port=9999)
    # Clear any existing test file
    if os.path.exists(bc.filename):
        os.remove(bc.filename)
    # Re-initialize to ensure a fresh state
    bc = Blockchain(port=9999)
    yield bc
    # Cleanup after tests
    if os.path.exists(bc.filename):
        os.remove(bc.filename)

def test_genesis_block(blockchain):
    assert len(blockchain.chain) == 1
    assert blockchain.chain[0]['previous_hash'] == '1'
    assert blockchain.chain[0]['proof'] == 100

def test_new_transaction_unsigned(blockchain):
    with pytest.raises(ValueError, match="Transaction must be signed"):
        blockchain.new_transaction("sender", "recipient", 10)

def test_new_transaction_invalid_signature(blockchain):
    private_key = SigningKey.generate(curve=SECP256k1)
    public_key = private_key.verifying_key
    public_key_hex = binascii.hexlify(public_key.to_string()).decode()

    with pytest.raises(ValueError, match="Invalid signature"):
        blockchain.new_transaction(public_key_hex, "recipient", 10, "invalid_signature")

def test_new_transaction_insufficient_balance(blockchain):
    private_key = SigningKey.generate(curve=SECP256k1)
    public_key = private_key.verifying_key
    public_key_hex = binascii.hexlify(public_key.to_string()).decode()

    transaction_data = {
        'sender': public_key_hex,
        'recipient': "recipient",
        'amount': 10,
    }
    transaction_string = json.dumps(transaction_data, sort_keys=True).encode()
    signature = binascii.hexlify(private_key.sign(transaction_string)).decode()

    with pytest.raises(ValueError, match="Insufficient balance"):
        blockchain.new_transaction(public_key_hex, "recipient", 10, signature)

def test_full_transaction_flow(blockchain):
    # 1. Create a wallet
    private_key = SigningKey.generate(curve=SECP256k1)
    public_key = private_key.verifying_key
    public_key_hex = binascii.hexlify(public_key.to_string()).decode()

    # 2. Mine a block to get some coins (reward)
    # The Reward transaction is added to current_transactions
    blockchain.new_transaction(sender="0", recipient=public_key_hex, amount=100)
    blockchain.new_block(proof=12345, previous_hash=blockchain.hash(blockchain.last_block))

    assert blockchain.get_balance(public_key_hex) == 100

    # 3. Create a signed transaction
    recipient_address = "recipient_abc"
    amount = 40
    transaction_data = {
        'sender': public_key_hex,
        'recipient': recipient_address,
        'amount': amount,
    }
    transaction_string = json.dumps(transaction_data, sort_keys=True).encode()
    signature = binascii.hexlify(private_key.sign(transaction_string)).decode()

    blockchain.new_transaction(public_key_hex, recipient_address, amount, signature)

    # Check balance before mining (includes pool)
    assert blockchain.get_balance(public_key_hex) == 60
    assert blockchain.get_balance(recipient_address) == 40

    # 4. Mine another block
    blockchain.new_block(proof=67890, previous_hash=blockchain.hash(blockchain.last_block))

    assert blockchain.get_balance(public_key_hex) == 60
    assert blockchain.get_balance(recipient_address) == 40
    assert len(blockchain.chain) == 3

def test_persistence(blockchain):
    private_key = SigningKey.generate(curve=SECP256k1)
    public_key_hex = binascii.hexlify(private_key.verifying_key.to_string()).decode()

    blockchain.new_transaction(sender="0", recipient=public_key_hex, amount=50)
    blockchain.new_block(proof=123, previous_hash=blockchain.hash(blockchain.last_block))

    # Create a new blockchain instance with same port
    new_bc = Blockchain(port=9999)
    assert len(new_bc.chain) == 2
    assert new_bc.get_balance(public_key_hex) == 50

def test_valid_chain(blockchain):
    private_key = SigningKey.generate(curve=SECP256k1)
    public_key_hex = binascii.hexlify(private_key.verifying_key.to_string()).decode()

    # Valid chain
    blockchain.new_transaction(sender="0", recipient=public_key_hex, amount=50)
    blockchain.new_block(proof=blockchain.proof_of_work(blockchain.last_block['proof']))
    # Add another block to ensure the previous block's hash is verified
    blockchain.new_block(proof=blockchain.proof_of_work(blockchain.last_block['proof']))

    assert blockchain.valid_chain(blockchain.chain) is True

    # Tamper with chain (block 1 is Genesis, block 2 is index 1)
    blockchain.chain[1]['transactions'][0]['amount'] = 1000
    assert blockchain.valid_chain(blockchain.chain) is False
