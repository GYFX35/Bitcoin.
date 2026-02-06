import pytest
from blockchain import app, blockchains, Blockchain

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_list_blockchains(client):
    response = client.get('/blockchains')
    assert response.status_code == 200
    data = response.get_json()
    assert 'blockchains' in data
    # Check for default blockchains
    names = [bc['name'] for bc in data['blockchains']]
    assert 'bitcoin' in names
    assert 'tether' in names
    assert 'news-coin' in names

def test_create_blockchain(client):
    response = client.post('/blockchains/new', json={
        'name': 'new-test-coin',
        'type': 'altcoin'
    })
    assert response.status_code == 201
    assert 'new-test-coin' in blockchains

def test_create_existing_blockchain(client):
    response = client.post('/blockchains/new', json={
        'name': 'bitcoin',
        'type': 'altcoin'
    })
    assert response.status_code == 400

def test_mine_on_specific_blockchain(client):
    # Mine on tether
    response = client.get('/mine?blockchain=tether')
    assert response.status_code == 200
    assert "New Block Forged on tether" in response.get_json()['message']

    # Check chain length of tether
    response = client.get('/chain?blockchain=tether')
    assert response.status_code == 200
    assert response.get_json()['length'] == 2

    # Check chain length of bitcoin (should still be 1 if not mined on)
    response = client.get('/chain?blockchain=bitcoin')
    assert response.status_code == 200
    assert response.get_json()['length'] == 1

def test_new_transaction_on_specific_blockchain(client):
    response = client.post('/transactions/new?blockchain=news-coin', json={
        'sender': 'A',
        'recipient': 'B',
        'amount': 100
    })
    assert response.status_code == 201
    assert "news-coin" in response.get_json()['message']

    # Mine to include transaction
    client.get('/mine?blockchain=news-coin')

    response = client.get('/chain?blockchain=news-coin')
    chain = response.get_json()['chain']
    assert len(chain[1]['transactions']) == 2 # Reward + our transaction
    assert chain[1]['transactions'][0]['amount'] == 100
    assert chain[1]['transactions'][1]['amount'] == 1
