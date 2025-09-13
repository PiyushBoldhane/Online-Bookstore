from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# Initialize database
def init_db():
    conn = sqlite3.connect("bookstore.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    author TEXT,
                    price REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER,
                    quantity INTEGER,
                    total REAL)''')
    conn.commit()

    # Sample books
    c.execute("SELECT COUNT(*) FROM books")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO books (title, author, price) VALUES (?, ?, ?)", [
            ("Atomic Habits", "James Clear", 350),
            ("The Alchemist", "Paulo Coelho", 299),
            ("Python Crash Course", "Eric Matthes", 600),
            ("Clean Code", "Robert C. Martin", 700)
        ])
    conn.commit()
    conn.close()

@app.route("/")
def index():
    conn = sqlite3.connect("bookstore.db")
    c = conn.cursor()
    c.execute("SELECT * FROM books")
    books = c.fetchall()
    conn.close()
    return render_template("index.html", books=books)

from flask import jsonify

@app.route('/add_to_cart/<int:book_id>', methods=['POST'])
def add_to_cart(book_id):
    cart = session.get('cart', {})

    if str(book_id) in cart:
        cart[str(book_id)] += 1
    else:
        cart[str(book_id)] = 1   # ✅ re-adds even if removed before

    session['cart'] = cart
    return jsonify({"success": True})


@app.route("/cart")
def cart():
    cart = session.get("cart", {})
    conn = sqlite3.connect("bookstore.db")
    c = conn.cursor()
    items, total = [], 0

    for book_id, qty in cart.items():
        c.execute("SELECT * FROM books WHERE id=?", (int(book_id),))  # back to int
        book = c.fetchone()
        if book:
            subtotal = book[3] * qty
            # now include book_id as first element
            items.append((book[0], book[1], book[2], book[3], qty, subtotal))
            total += subtotal

    conn.close()
    return render_template("cart.html", items=items, total=total)

@app.route("/checkout", methods=["POST"])
def checkout():
    cart = session.get("cart", {})
    customer_name = request.form.get("customer_name", "").strip()
    customer_email = request.form.get("customer_email", "").strip()

    if not cart:
        return render_template("order.html", error="❌ Your cart is empty. Please add items before checking out.")

    conn = sqlite3.connect("bookstore.db")
    c = conn.cursor()
    order_id = None
    try:
        conn.execute("BEGIN")
        total = 0
        for book_id, qty in cart.items():
            c.execute("SELECT price FROM books WHERE id=?", (book_id,))
            price = c.fetchone()[0]
            total += price * qty

        c.execute("INSERT INTO orders (customer_name, customer_email, total) VALUES (?, ?, ?)",
                  (customer_name, customer_email, total))
        order_id = c.lastrowid

        for book_id, qty in cart.items():
            c.execute("SELECT price FROM books WHERE id=?", (book_id,))
            price = c.fetchone()[0]
            c.execute("INSERT INTO order_items (order_id, book_id, quantity, price_at_purchase) VALUES (?, ?, ?, ?)",
                      (order_id, book_id, qty, price))

        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Transaction failed:", e)
    finally:
        conn.close()
        session["cart"] = {}

    return render_template("order.html", order_id=order_id)

@app.route("/remove_from_cart/<int:book_id>")
def remove_from_cart(book_id):
    cart = session.get("cart", {})
    book_id = str(book_id)  # Keep key as string
    if book_id in cart:
        del cart[book_id]   # Remove item completely
        session["cart"] = cart
    return redirect(url_for("cart"))

@app.route("/update_quantity/<int:book_id>/<action>")
def update_quantity(book_id, action):
    cart = session.get("cart", {})
    book_id = str(book_id)

    if book_id in cart:
        if action == "increase":
            cart[book_id] += 1
        elif action == "decrease":
            cart[book_id] -= 1
            if cart[book_id] <= 0:
                del cart[book_id]

    session["cart"] = cart
    return redirect(url_for("cart"))

@app.route("/place_order")
def place_order():
    session.pop("cart", None)
    return jsonify({"success": True, "message": "✅ Order placed successfully!"})

@app.route("/bill/<int:order_id>")
def bill(order_id):
    conn = sqlite3.connect("bookstore.db")
    c = conn.cursor()

    c.execute("SELECT customer_name, customer_email, total, created_at FROM orders WHERE id=?", (order_id,))
    order = c.fetchone()

    c.execute('''SELECT b.title, b.author, oi.quantity, oi.price_at_purchase
                 FROM order_items oi
                 JOIN books b ON oi.book_id = b.id
                 WHERE oi.order_id = ?''', (order_id,))
    items = c.fetchall()

    conn.close()
    return render_template("bill.html", order=order, items=items, order_id=order_id)

@app.route("/cart-data")
def cart_data():
    cart = session.get("cart", {})
    return jsonify({"cart": cart})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
