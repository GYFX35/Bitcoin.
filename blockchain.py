import hashlib
import json
import binascii
from ecdsa import SigningKey, VerifyingKey, SECP256k1
from argparse import ArgumentParser
from time import time
from urllib.parse import urlparse
from uuid import uuid4

import requests
from flask import Flask, jsonify, request, render_template

class Blockchain:
    def __init__(self, port=5000):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()
        self.difficulty = 4
        self.filename = f'blockchain_{port}.json'

        # Load chain from file or create genesis block
        if not self.load_chain():
            # Create the genesis block
            self.new_block(previous_hash='1', proof=100)

    def update_port(self, port):
        self.filename = f'blockchain_{port}.json'
        self.chain = []
        if not self.load_chain():
            self.new_block(previous_hash='1', proof=100)

    def new_block(self, proof, previous_hash=None):
        """
        Create a new Block in the Blockchain
        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New Block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        self.save_chain()
        return block

    def register_node(self, address):
        """
        Add a new node to the list of nodes
        :param address: <str> Address of node. Eg. 'http://192.168.0.5:5000'
        :return: None
        """

        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid
        :param chain: <list> A blockchain
        :return: <bool> True if valid, False if not
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            # Check that all transactions in the block are valid
            for transaction in block['transactions']:
                if transaction['sender'] != '0':
                    transaction_data = {
                        'sender': transaction['sender'],
                        'recipient': transaction['recipient'],
                        'amount': transaction['amount'],
                    }
                    if not self.verify_transaction(transaction['sender'], transaction['signature'], transaction_data):
                        return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.
        :return: <bool> True if our chain was replaced, False if not
        """

        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            try:
                response = requests.get(f'http://{node}/chain')

                if response.status_code == 200:
                    length = response.json()['length']
                    chain = response.json()['chain']

                    # Check if the length is longer and the chain is valid
                    if length > max_length and self.valid_chain(chain):
                        max_length = length
                        new_chain = chain
            except requests.exceptions.ConnectionError:
                # Skip nodes that are not reachable
                pass

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def new_transaction(self, sender, recipient, amount, signature=None):
        """
        Creates a new transaction to go into the next mined Block
        :param sender: <str> Address of the Sender (Public Key)
        :param recipient: <str> Address of the Recipient
        :param amount: <int> Amount
        :param signature: <str> Digital Signature
        :return: <int> The index of the Block that will hold this transaction
        """
        transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        }

        if sender != "0":
            if not signature:
                raise ValueError("Transaction must be signed")
            if not self.verify_transaction(sender, signature, transaction):
                raise ValueError("Invalid signature")

            # Check balance
            if self.get_balance(sender) < amount:
                raise ValueError("Insufficient balance")

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'signature': signature
        })

        self.save_chain()
        return self.last_block['index'] + 1

    @staticmethod
    def verify_transaction(public_key_hex, signature_hex, transaction_data):
        """
        Verifies a transaction signature
        """
        try:
            public_key = VerifyingKey.from_string(binascii.unhexlify(public_key_hex), curve=SECP256k1)
            signature = binascii.unhexlify(signature_hex)
            # Use sort_keys to ensure consistent JSON string
            transaction_string = json.dumps(transaction_data, sort_keys=True).encode()
            return public_key.verify(signature, transaction_string)
        except Exception:
            return False

    def proof_of_work(self, last_proof):
        """
        Simple Proof of Work Algorithm:
         - Find a number 'p' such that hash(pp') contains leading 4 zeroes, where p is the previous p'
         - p is the previous proof, and p' is the new proof
        :param last_proof: <int>
        :return: <int>
        """

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    def valid_proof(self, last_proof, proof):
        """
        Validates the proof: Does hash(last_proof, proof) contain leading zeroes?
        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :return: <bool> True if correct, False if not.
        """

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:self.difficulty] == "0" * self.difficulty

    def get_balance(self, address):
        """
        Calculates the balance of a given address
        """
        balance = 0
        for block in self.chain:
            for transaction in block['transactions']:
                if transaction['sender'] == address:
                    balance -= transaction['amount']
                if transaction['recipient'] == address:
                    balance += transaction['amount']

        # Also consider transactions in the current pool
        for transaction in self.current_transactions:
            if transaction['sender'] == address:
                balance -= transaction['amount']
            if transaction['recipient'] == address:
                balance += transaction['amount']

        return balance

    def save_chain(self):
        """
        Saves the chain and pending transactions to a JSON file
        """
        data = {
            'chain': self.chain,
            'current_transactions': self.current_transactions,
            'difficulty': self.difficulty
        }
        with open(self.filename, 'w') as f:
            json.dump(data, f, indent=4)

    def load_chain(self):
        """
        Loads the chain and pending transactions from a JSON file
        """
        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)
                # Handle old format where file only contained the chain list
                if isinstance(data, list):
                    self.chain = data
                else:
                    self.chain = data.get('chain', [])
                    self.current_transactions = data.get('current_transactions', [])
                    self.difficulty = data.get('difficulty', 4)
                return True
        except (FileNotFoundError, json.JSONDecodeError):
            return False

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block
        :param block: <dict> Block
        :return: <str>
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

# Instantiate our Node
app = Flask(__name__)

# Import and register the new blueprints
from facebook_integration import facebook_blueprint
from mql5_integration import mql5_blueprint

app.register_blueprint(facebook_blueprint)
app.register_blueprint(mql5_blueprint)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
import os
blockchain = Blockchain(port=os.environ.get('PORT', 5000))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/mine', methods=['GET'])
def mine():
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction_endpoint():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    try:
        index = blockchain.new_transaction(
            values['sender'],
            values['recipient'],
            values['amount'],
            values.get('signature')
        )
    except ValueError as e:
        return str(e), 400

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/balance/<address>', methods=['GET'])
def get_balance_endpoint(address):
    balance = blockchain.get_balance(address)
    response = {
        'address': address,
        'balance': balance,
    }
    return jsonify(response), 200


@app.route('/wallet/new', methods=['GET'])
def new_wallet():
    private_key = SigningKey.generate(curve=SECP256k1)
    public_key = private_key.verifying_key

    private_key_hex = binascii.hexlify(private_key.to_string()).decode()
    public_key_hex = binascii.hexlify(public_key.to_string()).decode()

    response = {
        'private_key': private_key_hex,
        'public_key': public_key_hex,
    }
    return jsonify(response), 200


@app.route('/difficulty', methods=['GET', 'POST'])
def difficulty():
    if request.method == 'POST':
        values = request.get_json()
        if not values or 'difficulty' not in values:
            return 'Missing difficulty value', 400

        try:
            new_difficulty = int(values.get('difficulty'))
            if new_difficulty < 1:
                return 'Difficulty must be at least 1', 400
            blockchain.difficulty = new_difficulty
            return jsonify({'message': f'Difficulty set to {new_difficulty}'}), 200
        except (ValueError, TypeError):
            return 'Invalid difficulty value. Must be an integer.', 400

    return jsonify({'difficulty': blockchain.difficulty}), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    blockchain.update_port(port)

    app.run(host='0.0.0.0', port=port)
