from flask import Flask, jsonify, request
import json
from datetime import datetime
import threading

app = Flask(__name__)

ITEMS_FILE = "items.json"
TRANSACTIONS_FILE = "transactions.json"
BANK_FILE = "bank.json"
lock = threading.Lock()

def read_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

def write_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

@app.route("/items", methods=["GET"])
def get_items():
    try:
        items = read_json(ITEMS_FILE)
        return jsonify(items)
    except Exception:
        return jsonify({"error": "Failed to load items"}), 500

@app.route("/transactions", methods=["GET"])
def get_transactions():
    try:
        transactions = read_json(TRANSACTIONS_FILE)
        return jsonify(transactions)
    except Exception:
        return jsonify({"error": "Failed to load transactions"}), 500

@app.route("/bank", methods=["GET"])
def get_bank():
    try:
        bank = read_json(BANK_FILE)
        return jsonify(bank)
    except Exception:
        return jsonify({"error": "Failed to load bank"}), 500

@app.route("/transactions", methods=["POST"])
def post_transaction():
    data = request.get_json(force=True)
    required_keys = {"credit_card_id", "credit_card_number", "items", "total"}
    if not data or not required_keys.issubset(data.keys()):
        return jsonify({"error": "Invalid transaction data"}), 400

    with lock:
        try:
            transactions = read_json(TRANSACTIONS_FILE)
            items = read_json(ITEMS_FILE)
            bank = read_json(BANK_FILE)
        except Exception:
            return jsonify({"error": "Failed to read data files"}), 500

        # Validate card
        card_id = data["credit_card_id"]
        card_number = data["credit_card_number"]
        if card_id not in bank:
            return jsonify({"error": "Card ID not found"}), 400
        if bank[card_id]["credit_card_number"] != card_number:
            return jsonify({"error": "Card number does not match ID"}), 400

        # Validate stock
        for cart_item in data["items"]:
            matched = next((i for i in items if i["item_id"] == cart_item["item_id"]), None)
            if not matched:
                return jsonify({"error": f"Item {cart_item['item_id']} not found"}), 400
            if matched["stock"] < cart_item["quantity"]:
                return jsonify({"error": f"Not enough stock for {matched['name']}"}), 400

        # Validate balance
        total = data["total"]
        if bank[card_id]["balance"] < total:
            return jsonify({"error": "Insufficient funds"}), 400

        # Charge the card
        bank[card_id]["balance"] -= total

        # Update stock
        for cart_item in data["items"]:
            for item in items:
                if item["item_id"] == cart_item["item_id"]:
                    item["stock"] -= cart_item["quantity"]

        # Add transaction
        last_id = transactions[-1]["id"] if transactions else 0
        new_id = last_id + 1
        transaction = {
            "id": new_id,
            "timestamp": datetime.now().isoformat(),
            "credit_card_id": card_id,
            "credit_card_number": card_number,
            "items": data["items"],
            "total": total,
            "refunded": False
        }
        transactions.append(transaction)

        try:
            write_json(TRANSACTIONS_FILE, transactions)
            write_json(ITEMS_FILE, items)
            write_json(BANK_FILE, bank)
        except Exception:
            return jsonify({"error": "Failed to save updated data"}), 500

    return jsonify({"status": "success", "id": new_id}), 200

@app.route("/transactions/refund", methods=["POST"])
def refund_transaction():
    data = request.get_json(force=True)
    tid = data.get("transaction_id")
    if tid is None:
        return jsonify({"error": "Missing transaction_id"}), 400

    with lock:
        try:
            transactions = read_json(TRANSACTIONS_FILE)
            items = read_json(ITEMS_FILE)
            bank = read_json(BANK_FILE)
        except Exception:
            return jsonify({"error": "Failed to read data files"}), 500

        transaction = next((t for t in transactions if t["id"] == tid), None)
        if transaction is None:
            return jsonify({"error": "Transaction not found"}), 404
        if transaction.get("refunded", False):
            return jsonify({"error": "Transaction already refunded"}), 400

        card_id = transaction["credit_card_id"]
        refund_amount = transaction["total"]

        if card_id not in bank:
            return jsonify({"error": "Credit card not found in bank"}), 400

        # Restock items
        for cart_item in transaction["items"]:
            for item in items:
                if item["item_id"] == cart_item["item_id"]:
                    item["stock"] += cart_item["quantity"]

        # Refund balance
        bank[card_id]["balance"] += refund_amount

        # Update transaction
        transaction["refunded"] = True

        try:
            write_json(TRANSACTIONS_FILE, transactions)
            write_json(ITEMS_FILE, items)
            write_json(BANK_FILE, bank)
        except Exception:
            return jsonify({"error": "Failed to save refund"}), 500

    return jsonify({"status": "refund_success", "id": tid}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
