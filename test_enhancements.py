import pytest
import requests
import time
import subprocess
import os
import binascii
from ecdsa import SigningKey, SECP256k1

@pytest.fixture(scope="module")
def server():
    # Clean up state files before starting
    for f in os.listdir('.'):
        if f.startswith('blockchain_') and f.endswith('.json'):
            os.remove(f)

    # Start the server in background
    server_process = subprocess.Popen(["python3", "blockchain.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2) # Wait for server to start
    yield "http://127.0.0.1:5000"
    server_process.terminate()

    # Clean up state files after finishing
    for f in os.listdir('.'):
        if f.startswith('blockchain_') and f.endswith('.json'):
            os.remove(f)

def test_multi_chain_registry(server):
    base_url = server
    response = requests.get(f"{base_url}/blockchains")
    assert response.status_code == 200
    data = response.json()
    assert 'main' in data['blockchains']
    assert 'supply_chain' in data['blockchains']
    assert 'altcoin' in data['blockchains']

def test_create_new_chain(server):
    base_url = server
    payload = {"name": "test_coin"}
    response = requests.post(f"{base_url}/blockchains/new", json=payload)
    assert response.status_code == 201

    response = requests.get(f"{base_url}/chain?blockchain=test_coin")
    assert response.status_code == 200
    assert response.json()['blockchain'] == 'test_coin'

def test_create_new_chain_invalid_name(server):
    base_url = server
    payload = {"name": "invalid/name"}
    response = requests.post(f"{base_url}/blockchains/new", json=payload)
    assert response.status_code == 400
    assert "Invalid characters" in response.text

def test_supply_chain_item_tracking(server):
    base_url = server
    # Add item
    payload = {
        "sender": "0",
        "recipient": "Warehouse_A",
        "item_id": "item_789",
        "status": "manufactured",
        "location": "Factory_X"
    }
    response = requests.post(f"{base_url}/supply_chain/add_item", json=payload)
    assert response.status_code == 201

    # Mine to include it
    requests.get(f"{base_url}/mine?blockchain=supply_chain")

    # Get history
    response = requests.get(f"{base_url}/supply_chain/item/item_789")
    assert response.status_code == 200
    data = response.json()
    assert data['item_id'] == 'item_789'
    assert len(data['history']) == 1
    assert data['history'][0]['status'] == 'manufactured'

def test_balance_all(server):
    base_url = server
    # Address doesn't matter much for this test as long as it's valid hex if we want to sign,
    # but balance_all just returns 0s for a new address
    address = "test_address"
    response = requests.get(f"{base_url}/balance_all/{address}")
    assert response.status_code == 200
    data = response.json()
    assert 'main' in data['balances']
    assert 'supply_chain' in data['balances']
