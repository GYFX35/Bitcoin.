# Simple Blockchain

This repository contains a simple implementation of a blockchain in Python. It's designed for educational purposes to demonstrate the core concepts of cryptocurrencies.

The implementation includes:
- A `Blockchain` class with all the core logic.
- A Flask-based web server exposing a REST API.
- A simple HTML frontend to interact with the blockchain.
- A peer-to-peer networking model with a consensus algorithm.

## Installation

1.  Clone the repository:
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Blockchain Node

You can run a node by executing the `blockchain.py` script:

```bash
python blockchain.py
```

By default, the node will run on `http://127.0.0.1:5000`.

## API Endpoints

The following endpoints are available:

-   `GET /`: View the HTML user interface.
-   `GET /mine`: Mine a new block.
-   `POST /transactions/new`: Add a new transaction to the pool.
    -   **Body:** `{"sender": "...", "recipient": "...", "amount": ...}`
-   `GET /chain`: Get the full blockchain.
-   `POST /nodes/register`: Register one or more new nodes.
    -   **Body:** `{"nodes": ["http://127.0.0.1:5001"]}`
-   `GET /nodes/resolve`: Run the consensus algorithm to resolve conflicts.

## Testing the P2P Network

To see the decentralization and consensus algorithm in action, you can run multiple nodes on the same machine.

1.  **Start two nodes on different ports:**

    In your first terminal:
    ```bash
    python blockchain.py -p 5000
    ```

    In your second terminal:
    ```bash
    python blockchain.py -p 5001
    ```

2.  **Register the nodes with each other:**

    On the first node (port 5000), register the second node (port 5001). You can use a tool like `curl`:
    ```bash
    curl -X POST -H "Content-Type: application/json" -d '{"nodes": ["http://127.0.0.1:5001"]}' http://127.0.0.1:5000/nodes/register
    ```

3.  **Create divergent chains:**

    -   Mine a block on node 5000. This will give it a chain of length 2.
        ```bash
        curl http://127.0.0.1:5000/mine
        ```
    -   Mine two blocks on node 5001. This will give it a longer chain of length 3.
        ```bash
        curl http://127.0.0.1:5001/mine
        curl http://127.0.0.1:5001/mine
        ```

4.  **Run the consensus algorithm:**

    Now, if you ask node 5000 to resolve conflicts, it will see that node 5001 has a longer, valid chain and will replace its own.
    ```bash
    curl http://127.0.0.1:5000/nodes/resolve
    ```

    You can then check the chain on node 5000, and you will see it has been updated to the longer chain from node 5001.
    ```bash
    curl http://127.0.0.1:5000/chain
    ```

## Deployment to Heroku

This project is set up for automatic deployment to Heroku using GitHub Actions.

### Prerequisites

1.  A Heroku account.
2.  The Heroku CLI (optional, but helpful for debugging).

### Setup Instructions

1.  **Create a Heroku App:**
    -   Go to your Heroku dashboard and create a new app.
    -   Choose a unique name for your app (e.g., `my-simple-blockchain`). This will be your `HEROKU_APP_NAME`.

2.  **Get your Heroku API Key:**
    -   Go to your Heroku Account Settings page.
    -   Scroll down to the "API Key" section and click "Reveal" to see your API key. This will be your `HEROKU_API_KEY`.

3.  **Configure GitHub Secrets:**
    -   In your GitHub repository, go to `Settings > Secrets and variables > Actions`.
    -   Click `New repository secret` to add the following secrets:
        -   `HEROKU_APP_NAME`: The name of the Heroku app you created.
        -   `HEROKU_API_KEY`: Your Heroku API key.
        -   `HEROKU_EMAIL`: The email address you use for your Heroku account.

4.  **Deploy:**
    -   Once the secrets are configured, the deployment will automatically trigger every time you push a new commit to the `main` branch.
    -   You can monitor the deployment progress in the "Actions" tab of your GitHub repository.
