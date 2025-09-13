PRAGMA foreign_keys = ON;

-- Books Table (3NF compliant)
CREATE TABLE IF NOT EXISTS books (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  author TEXT,
  price REAL NOT NULL,
  stock INTEGER DEFAULT 0 CHECK (stock >= 0),
  description TEXT
);

-- Orders Table
CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_name TEXT NOT NULL,
  customer_email TEXT NOT NULL UNIQUE,
  total REAL NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Order Items Table
CREATE TABLE IF NOT EXISTS order_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER NOT NULL,
  book_id INTEGER NOT NULL,
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  price_at_purchase REAL NOT NULL,
  FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
  FOREIGN KEY(book_id) REFERENCES books(id)
);

-- Indexes for performance
CREATE INDEX idx_order_id ON order_items(order_id);
CREATE INDEX idx_book_id ON order_items(book_id);

-- View for order summary
CREATE VIEW IF NOT EXISTS order_summary AS
SELECT o.id AS order_id, o.customer_name, o.total, o.created_at
FROM orders o;

-- Sample Data
INSERT INTO books (title, author, price, stock, description) VALUES
('Clean Code', 'Robert C. Martin', 299.0, 5, 'A Handbook of Agile Software Craftsmanship'),
('Introduction to Algorithms', 'Cormen et al.', 799.0, 2, 'Comprehensive algorithms book'),
('The Pragmatic Programmer', 'Andrew Hunt', 399.0, 4, 'Classic software engineering book');