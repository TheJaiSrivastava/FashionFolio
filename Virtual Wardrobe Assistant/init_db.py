import os
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash

# Ensure the instance directory exists
os.makedirs('instance', exist_ok=True)

# Connect to the database
conn = sqlite3.connect('instance/wardrobe.db')
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

# Create tables
tables = [
    '''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL,
        location TEXT,
        style_preference TEXT
    )
    ''',
    
    '''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT
    )
    ''',
    
    '''
    CREATE TABLE IF NOT EXISTS colors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        hex_code TEXT
    )
    ''',
    
    '''
    CREATE TABLE IF NOT EXISTS clothing_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category_id INTEGER NOT NULL,
        color_id INTEGER NOT NULL,
        season TEXT,
        description TEXT,
        brand TEXT,
        image_path TEXT,
        user_id INTEGER NOT NULL,
        created_at TIMESTAMP NOT NULL,
        FOREIGN KEY (category_id) REFERENCES categories (id),
        FOREIGN KEY (color_id) REFERENCES colors (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''',
    
    '''
    CREATE TABLE IF NOT EXISTS outfits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        occasion TEXT,
        season TEXT,
        is_favorite BOOLEAN DEFAULT 0,
        user_id INTEGER NOT NULL,
        created_at TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''',
    
    '''
    CREATE TABLE IF NOT EXISTS outfit_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        outfit_id INTEGER NOT NULL,
        clothing_item_id INTEGER NOT NULL,
        FOREIGN KEY (outfit_id) REFERENCES outfits (id),
        FOREIGN KEY (clothing_item_id) REFERENCES clothing_items (id)
    )
    ''',
    
    '''
    CREATE TABLE IF NOT EXISTS wear_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        clothing_item_id INTEGER,
        outfit_id INTEGER,
        date TIMESTAMP NOT NULL,
        notes TEXT,
        weather_condition TEXT,
        temperature REAL,
        created_at TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (clothing_item_id) REFERENCES clothing_items (id),
        FOREIGN KEY (outfit_id) REFERENCES outfits (id)
    )
    '''
]

for table in tables:
    cursor.execute(table)
    
# Insert initial data

# Categories
categories = [
    ('Tops', 'Shirts, t-shirts, blouses, etc.'),
    ('Bottoms', 'Pants, shorts, skirts, etc.'),
    ('Dresses', 'All types of dresses'),
    ('Outerwear', 'Jackets, coats, sweaters, etc.'),
    ('Footwear', 'Shoes, boots, sandals, etc.'),
    ('Accessories', 'Hats, scarves, belts, etc.')
]

cursor.executemany('INSERT OR IGNORE INTO categories (name, description) VALUES (?, ?)', categories)

# Colors
colors = [
    ('Black', '#000000'),
    ('White', '#FFFFFF'),
    ('Red', '#FF0000'),
    ('Blue', '#0000FF'),
    ('Green', '#00FF00'),
    ('Yellow', '#FFFF00'),
    ('Brown', '#A52A2A'),
    ('Grey', '#808080'),
    ('Navy', '#000080'),
    ('Purple', '#800080'),
    ('Pink', '#FFC0CB'),
    ('Orange', '#FFA500')
]

cursor.executemany('INSERT OR IGNORE INTO colors (name, hex_code) VALUES (?, ?)', colors)

# Create demo user
hashed_password = generate_password_hash('password123')
cursor.execute('INSERT OR IGNORE INTO users (username, email, password_hash, created_at, location, style_preference) VALUES (?, ?, ?, ?, ?, ?)',
             ('demo', 'demo@example.com', hashed_password, datetime.utcnow(), 'New York, USA', 'Casual'))

# Get the demo user ID
cursor.execute('SELECT id FROM users WHERE username = ?', ('demo',))
user_id = cursor.fetchone()[0]

# Add some sample clothing items
sample_items = [
    ('Blue Jeans', 2, 4, 'All Season', 'Classic blue denim jeans', 'Levi\'s', None, user_id, datetime.utcnow()),
    ('White T-Shirt', 1, 2, 'Summer', 'Basic cotton t-shirt', 'H&M', None, user_id, datetime.utcnow()),
    ('Black Blazer', 4, 1, 'Fall', 'Formal black blazer', 'Zara', None, user_id, datetime.utcnow()),
    ('Sneakers', 5, 2, 'All Season', 'Casual white sneakers', 'Nike', None, user_id, datetime.utcnow()),
    ('Red Dress', 3, 3, 'Summer', 'Elegant red dress for special occasions', 'Ralph Lauren', None, user_id, datetime.utcnow())
]

cursor.executemany('''
    INSERT OR IGNORE INTO clothing_items (name, category_id, color_id, season, description, brand, image_path, user_id, created_at) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
''', sample_items)

# Add sample outfit
cursor.execute('''
    INSERT OR IGNORE INTO outfits (name, description, occasion, season, is_favorite, user_id, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
''', ('Casual Day Out', 'Perfect for weekend errands', 'Casual', 'Spring', 1, user_id, datetime.utcnow()))

# Get the outfit ID
cursor.execute('SELECT id FROM outfits WHERE name = ? AND user_id = ?', ('Casual Day Out', user_id))
outfit_id = cursor.fetchone()[0]

# Get clothing item IDs for the outfit
cursor.execute('SELECT id FROM clothing_items WHERE name = ? AND user_id = ?', ('Blue Jeans', user_id))
jeans_id = cursor.fetchone()[0]

cursor.execute('SELECT id FROM clothing_items WHERE name = ? AND user_id = ?', ('White T-Shirt', user_id))
tshirt_id = cursor.fetchone()[0]

cursor.execute('SELECT id FROM clothing_items WHERE name = ? AND user_id = ?', ('Sneakers', user_id))
sneakers_id = cursor.fetchone()[0]

# Add items to the outfit
outfit_items = [
    (outfit_id, jeans_id),
    (outfit_id, tshirt_id),
    (outfit_id, sneakers_id)
]

cursor.executemany('INSERT OR IGNORE INTO outfit_items (outfit_id, clothing_item_id) VALUES (?, ?)', outfit_items)

# Commit changes and close the connection
conn.commit()
conn.close()

print("Database initialized successfully with sample data!")
print("You can now run the application using: streamlit run streamlit_app.py")
print("Login with:")
print("  Username: demo")
print("  Password: password123") 