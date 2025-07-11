import tkinter as tk
from tkinter import ttk
import requests

SERVER_URL = "http://10.10.0.193:5000"  # Change as needed

class POSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("POS System")
        self.root.attributes("-fullscreen", True)

        self.items = []
        self.cart = []
        self.transactions = []

        # Create frames for pages
        self.main_frame = tk.Frame(root)
        self.payment_frame = tk.Frame(root)
        self.message_frame = tk.Frame(root)

        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.build_main_ui()
        self.build_payment_ui()
        self.build_message_ui()

        self.load_items()
        self.load_transactions()

    # --- Main Page ---
    def build_main_ui(self):
        left_frame = tk.Frame(self.main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(left_frame, text="Available Items", font=("Arial", 18)).pack(pady=10)

        self.items_canvas = tk.Canvas(left_frame, height=300)
        self.items_scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.items_canvas.yview)
        self.items_list_frame = tk.Frame(self.items_canvas)

        self.items_list_frame.bind(
            "<Configure>",
            lambda e: self.items_canvas.configure(scrollregion=self.items_canvas.bbox("all"))
        )

        self.items_canvas.create_window((0, 0), window=self.items_list_frame, anchor="nw")
        self.items_canvas.configure(yscrollcommand=self.items_scrollbar.set)

        self.items_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.items_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        manual_frame = tk.Frame(left_frame)
        manual_frame.pack(pady=10)
        tk.Label(manual_frame, text="Add Item by ID:").pack(side=tk.LEFT)
        self.manual_item_id_entry = tk.Entry(manual_frame, width=10)
        self.manual_item_id_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(manual_frame, text="Add", command=self.add_manual_item).pack(side=tk.LEFT)

        tk.Label(left_frame, text="Cart", font=("Arial", 18)).pack(pady=10)
        self.cart_listbox = tk.Listbox(left_frame, width=50, height=10)
        self.cart_listbox.pack()
        tk.Button(left_frame, text="Remove Selected Item", command=self.remove_selected_cart_item).pack(pady=5)
        self.total_var = tk.StringVar()
        self.total_var.set("Total: $0.00")
        tk.Label(left_frame, textvariable=self.total_var, font=("Arial", 14)).pack(pady=5)
        tk.Button(left_frame, text="Pay", command=self.show_payment_page).pack(pady=5)

        right_frame = tk.Frame(self.main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(right_frame, text="Transactions", font=("Arial", 18)).pack(pady=10)
        self.trans_tree = ttk.Treeview(right_frame, columns=("id", "total", "refunded"), show="headings", height=15)
        self.trans_tree.heading("id", text="ID")
        self.trans_tree.heading("total", text="Total ($)")
        self.trans_tree.heading("refunded", text="Refunded")
        self.trans_tree.column("id", width=50)
        self.trans_tree.column("total", width=80)
        self.trans_tree.column("refunded", width=80)
        self.trans_tree.pack(fill=tk.BOTH, expand=True)
        tk.Button(right_frame, text="Refund Selected Transaction", command=self.refund_selected_transaction).pack(pady=5)
        tk.Button(right_frame, text="Exit Fullscreen", command=self.exit_fullscreen).pack(pady=10)

    # --- Payment Page ---
    def build_payment_ui(self):
        tk.Label(self.payment_frame, text="Enter Credit Card Number:", font=("Arial", 18)).pack(pady=20)
        self.card_entry = tk.Entry(self.payment_frame, font=("Arial", 16))
        self.card_entry.pack()

        self.payment_message_label = tk.Label(self.payment_frame, font=("Arial", 14), fg="red")
        self.payment_message_label.pack(pady=10)

        btn_frame = tk.Frame(self.payment_frame)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Confirm Purchase", command=self.confirm_payment).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Back to Cart", command=self.show_main_page).pack(side=tk.LEFT, padx=10)

    # --- Message Page ---
    def build_message_ui(self):
        self.message_label = tk.Label(self.message_frame, font=("Arial", 20), wraplength=600)
        self.message_label.pack(pady=100)

    def show_message(self, message):
        self.main_frame.pack_forget()
        self.payment_frame.pack_forget()
        self.message_frame.pack(fill=tk.BOTH, expand=True)

        self.message_label.config(text=message)
        for widget in self.message_frame.pack_slaves():
            if isinstance(widget, tk.Frame):
                widget.destroy()

        btn_frame = tk.Frame(self.message_frame)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Back to Main", command=self.show_main_page).pack()

    # --- Page Switch ---
    def show_main_page(self):
        self.payment_frame.pack_forget()
        self.message_frame.pack_forget()
        self.main_frame.pack(fill=tk.BOTH, expand=True)

    def show_payment_page(self):
        if not self.cart:
            self.show_message("Cart is empty! Add items before paying.")
            return
        self.main_frame.pack_forget()
        self.payment_message_label.config(text="")
        self.card_entry.delete(0, tk.END)
        self.payment_frame.pack(fill=tk.BOTH, expand=True)

    def exit_fullscreen(self):
        self.root.attributes("-fullscreen", False)

    def load_items(self):
        try:
            response = requests.get(f"{SERVER_URL}/items")
            self.items = response.json()
            self.build_items_ui()
        except:
            self.items = []

    def build_items_ui(self):
        for widget in self.items_list_frame.winfo_children():
            widget.destroy()

        for item in self.items:
            if item["stock"] <= 0:
                continue
            frame = tk.Frame(self.items_list_frame, relief=tk.RIDGE, borderwidth=1)
            frame.pack(fill=tk.X, pady=2, padx=2)
            tk.Label(frame, text=item["name"], font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
            tk.Label(frame, text=f"${item['price']:.2f}", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
            tk.Label(frame, text=f"Stock: {item['stock']}", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
            tk.Button(frame, text="Add", command=lambda i=item: self.add_to_cart(i)).pack(side=tk.RIGHT, padx=5)

    def load_transactions(self):
        try:
            response = requests.get(f"{SERVER_URL}/transactions")
            self.transactions = response.json()
            self.build_transactions_ui()
        except:
            self.transactions = []

    def build_transactions_ui(self):
        for i in self.trans_tree.get_children():
            self.trans_tree.delete(i)
        for t in self.transactions:
            refunded_text = "Yes" if t.get("refunded", False) else "No"
            self.trans_tree.insert("", "end", values=(t["id"], f"{t['total']:.2f}", refunded_text))

    def add_to_cart(self, item):
        cart_item = next((c for c in self.cart if c["item_id"] == item["item_id"]), None)
        if cart_item:
            if cart_item["quantity"] < item["stock"]:
                cart_item["quantity"] += 1
            else:
                self.show_message(f"No more stock for {item['name']}")
                return
        else:
            if item["stock"] > 0:
                self.cart.append({
                    "item_id": item["item_id"],
                    "name": item["name"],
                    "price": item["price"],
                    "quantity": 1
                })
            else:
                self.show_message(f"{item['name']} is out of stock")
                return
        self.update_cart_display()

    def add_manual_item(self):
        item_id = self.manual_item_id_entry.get().strip()
        if not item_id:
            return
        item = next((i for i in self.items if i["item_id"].lower() == item_id.lower()), None)
        if not item:
            self.show_message(f"Item ID '{item_id}' not found.")
            return
        self.add_to_cart(item)
        self.manual_item_id_entry.delete(0, tk.END)

    def remove_selected_cart_item(self):
        selected = self.cart_listbox.curselection()
        if not selected:
            return
        index = selected[0]
        self.cart.pop(index)
        self.update_cart_display()

    def update_cart_display(self):
        self.cart_listbox.delete(0, tk.END)
        total = 0.0
        for c in self.cart:
            line = f"{c['name']} x{c['quantity']} - ${c['price']*c['quantity']:.2f}"
            self.cart_listbox.insert(tk.END, line)
            total += c['price'] * c['quantity']
        self.total_var.set(f"Total: ${total:.2f}")

    def confirm_payment(self):
        card_number = self.card_entry.get().strip()
        if not card_number:
            self.payment_message_label.config(text="Please enter a credit card number.")
            return

        try:
            bank = requests.get(f"{SERVER_URL}/bank").json()
        except:
            self.payment_message_label.config(text="Failed to connect to server.")
            return

        found_card = None
        for card_id, card in bank.items():
            if card["credit_card_number"] == card_number:
                found_card = {"id": card_id, **card}
                break

        if not found_card:
            self.payment_message_label.config(text="Card number not found.")
            return

        total = sum(c['price'] * c['quantity'] for c in self.cart)
        if found_card["balance"] < total:
            self.payment_message_label.config(text=f"Insufficient funds. Balance: ${found_card['balance']:.2f}")
            return

        transaction = {
            "credit_card_id": found_card["id"],
            "credit_card_number": card_number,
            "items": self.cart,
            "total": total,
            "refunded": False
        }

        try:
            response = requests.post(f"{SERVER_URL}/transactions", json=transaction)
            res_json = response.json()
        except:
            self.payment_message_label.config(text="Failed to send transaction.")
            return

        if res_json.get("status") == "success":
            self.payment_message_label.config(text=f"Transaction #{res_json.get('id')} completed successfully.", fg="green")
            self.cart.clear()
            self.load_items()
            self.update_cart_display()
            self.load_transactions()
        else:
            self.payment_message_label.config(text="Transaction failed.")

    def refund_selected_transaction(self):
        selected = self.trans_tree.selection()
        if not selected:
            self.show_message("Select a transaction to refund.")
            return
        item = selected[0]
        tid = int(self.trans_tree.item(item, "values")[0])

        transaction = next((t for t in self.transactions if t["id"] == tid), None)
        if transaction is None:
            self.show_message("Transaction not found.")
            return
        if transaction.get("refunded", False):
            self.show_message("This transaction has already been refunded.")
            return

        self.show_refund_confirm(f"Refund transaction #{tid} for ${transaction['total']:.2f}?", tid)

    def show_refund_confirm(self, message, tid):
        self.main_frame.pack_forget()
        self.payment_frame.pack_forget()
        self.message_frame.pack(fill=tk.BOTH, expand=True)

        self.message_label.config(text=message, fg="black")

        for widget in self.message_frame.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.destroy()

        btn_frame = tk.Frame(self.message_frame)
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="Refund", command=lambda: self.do_refund(tid)).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Cancel", command=self.show_main_page).pack(side=tk.LEFT, padx=10)

    def do_refund(self, tid):
        try:
            response = requests.post(f"{SERVER_URL}/transactions/refund", json={"transaction_id": tid})
            res_json = response.json()
        except:
            self.show_message("Refund request failed.")
            return

        if res_json.get("status") == "refund_success":
            self.show_message(f"Transaction #{tid} refunded successfully.")
            self.load_items()
            self.load_transactions()
        else:
            self.show_message("Refund failed.")

def main():
    root = tk.Tk()
    app = POSApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
