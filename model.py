# model.py
import sqlite3

class SuperstoreModel:
    def __init__(self, db_name="database.db"):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row  # Allows accessing rows by column name
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self):
        conn = self.get_connection()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER NOT NULL,
                category_id INTEGER,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            );
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL
            );
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_amount REAL,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            );
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                product_id INTEGER,
                quantity INTEGER NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            );
        """)
        # Seed default categories if empty
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM categories")
        if cur.fetchone()[0] == 0:
            cur.executemany("INSERT INTO categories (name) VALUES (?)", [
                ("Groceries",), ("Electronics",), ("Stationery",)
            ])
            conn.commit()
        conn.close()

    def get_all_products(self):
        conn = self.get_connection()
        products = conn.execute("""
            SELECT p.id, p.name, p.price, p.stock, c.name as category 
            FROM products p LEFT JOIN categories c ON p.category_id = c.id
        """).fetchall()
        conn.close()
        return [dict(row) for row in products]

    def add_product(self, name, price, stock, category_id):
        conn = self.get_connection()
        try:
            conn.execute(
                "INSERT INTO products (name, price, stock, category_id) VALUES (?, ?, ?, ?)",
                (name, float(price), int(stock), int(category_id))
            )
            conn.commit()
            conn.close()
            return True, "Product added successfully!"
        except Exception as e:
            conn.close()
            return False, str(e)

    def get_all_customers(self):
        conn = self.get_connection()
        customers = conn.execute("SELECT id, name, email FROM customers").fetchall()
        conn.close()
        return [dict(row) for row in customers]

    def add_customer(self, name, email):
        conn = self.get_connection()
        try:
            conn.execute(
                "INSERT INTO customers (name, email) VALUES (?, ?)",
                (name, email)
            )
            conn.commit()
            conn.close()
            return True, "Customer registered successfully!"
        except sqlite3.IntegrityError:
            conn.close()
            return False, "Error: Email already exists."
        except Exception as e:
            conn.close()
            return False, str(e)

    def place_order(self, customer_id, product_id, quantity):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Check stock
            cursor.execute("SELECT name, price, stock FROM products WHERE id = ?", (product_id,))
            product = cursor.fetchone()
            if not product:
                conn.close()
                return False, "Product not found."
            
            name, price, stock = product['name'], product['price'], product['stock']
            if stock < quantity:
                conn.close()
                return False, f"Insufficient stock for {name}! Available: {stock}"
            
            subtotal = price * quantity
            
            # Create order header
            cursor.execute(
                "INSERT INTO orders (customer_id, total_amount) VALUES (?, ?)",
                (customer_id, subtotal)
            )
            order_id = cursor.lastrowid
            
            # Create order item
            cursor.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, subtotal) VALUES (?, ?, ?, ?)",
                (order_id, product_id, quantity, subtotal)
            )
            
            # Deduct stock
            cursor.execute(
                "UPDATE products SET stock = stock - ? WHERE id = ?",
                (quantity, product_id)
            )
            
            conn.commit()
            conn.close()
            return True, f"Order #{order_id} placed successfully! Total: ${subtotal:.2f}"
        except Exception as e:
            conn.close()
            return False, f"Transaction failed: {str(e)}"

    def get_sales_report(self):
        conn = self.get_connection()
        orders = conn.execute("""
            SELECT o.id, c.name as customer_name, o.order_date, o.total_amount
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
        """).fetchall()
        conn.close()
        return [dict(row) for row in orders]