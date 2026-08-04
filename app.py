from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import os
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = 'ecoshop_secret_key_2026'

# ========== DATABASE SETUP ==========
DB_NAME = 'ecoshop.db'

def init_db():
    """Initialize database with all data"""
    print("🔄 Creating database...")
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Drop existing tables if they exist (fresh start)
    c.execute('DROP TABLE IF EXISTS sale_items')
    c.execute('DROP TABLE IF EXISTS sales')
    c.execute('DROP TABLE IF EXISTS products')
    c.execute('DROP TABLE IF EXISTS categories')
    c.execute('DROP TABLE IF EXISTS employees')
    
    # Create tables
    c.execute('''
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_ru TEXT, name_en TEXT, icon TEXT, color TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE, name_ru TEXT, name_en TEXT,
            price REAL, cost REAL, quantity INTEGER DEFAULT 0, category_id INTEGER
        )
    ''')
    
    c.execute('''
        CREATE TABLE employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT UNIQUE, name TEXT, password TEXT, role TEXT, status TEXT DEFAULT 'Active'
        )
    ''')
    
    c.execute('''
        CREATE TABLE sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT UNIQUE, employee_id TEXT, customer_name TEXT,
            sale_date DATETIME, total_amount REAL, discount REAL DEFAULT 0, payment_method TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER, product_id INTEGER, quantity INTEGER, price REAL
        )
    ''')
    
    # Insert employees
    c.execute('INSERT INTO employees (employee_id, name, password, role) VALUES (?, ?, ?, ?)',
              ('ADMIN001', 'Admin', 'admin123', 'Admin'))
    c.execute('INSERT INTO employees (employee_id, name, password, role) VALUES (?, ?, ?, ?)',
              ('EMP001', 'Zubair', 'staff123', 'Staff'))
    
    # Insert categories
    categories = [
        ('Молочные продукты', 'Dairy', '🥛', '#FF9800'),
        ('Напитки', 'Beverages', '🥤', '#2196F3'),
        ('Продукты питания', 'Groceries', '🥫', '#4CAF50'),
        ('Хлеб и выпечка', 'Bakery', '🍞', '#FFC107'),
        ('Сладости', 'Sweets', '🍫', '#E91E63'),
        ('Мясо и рыба', 'Meat & Fish', '🥩', '#F44336'),
        ('Овощи и фрукты', 'Fruits & Vegetables', '🥬', '#8BC34A'),
        ('Бытовая химия', 'Household', '🧹', '#9E9E9E'),
        ('Электроника', 'Electronics', '📱', '#3F51B5'),
        ('Одежда', 'Clothing', '👕', '#FF5722'),
        ('Косметика', 'Cosmetics', '💄', '#E91E63'),
        ('Другое', 'Other', '📦', '#607D8B'),
    ]
    c.executemany('INSERT INTO categories (name_ru, name_en, icon, color) VALUES (?, ?, ?, ?)', categories)
    
    # Insert 60 products
    products = [
        ('1001', 'Молоко 1л', 'Milk 1L', 120, 80, 50, 'Dairy'),
        ('1002', 'Йогурт', 'Yogurt', 85, 55, 30, 'Dairy'),
        ('1003', 'Сыр 200г', 'Cheese', 250, 180, 20, 'Dairy'),
        ('1004', 'Сметана', 'Sour Cream', 95, 65, 25, 'Dairy'),
        ('1005', 'Масло', 'Butter', 180, 130, 15, 'Dairy'),
        ('2001', 'Кока-Кола', 'Coca-Cola', 150, 100, 40, 'Beverages'),
        ('2002', 'Вода', 'Mineral Water', 60, 35, 100, 'Beverages'),
        ('2003', 'Сок', 'Orange Juice', 200, 140, 25, 'Beverages'),
        ('2004', 'Чай', 'Black Tea', 120, 80, 30, 'Beverages'),
        ('2005', 'Кофе', 'Instant Coffee', 350, 250, 20, 'Beverages'),
        ('3001', 'Рис 1кг', 'Rice', 180, 120, 60, 'Groceries'),
        ('3002', 'Макароны', 'Pasta', 90, 60, 45, 'Groceries'),
        ('3003', 'Масло растительное', 'Sunflower Oil', 220, 160, 35, 'Groceries'),
        ('3004', 'Мука', 'Flour', 95, 65, 50, 'Groceries'),
        ('3005', 'Сахар', 'Sugar', 110, 75, 40, 'Groceries'),
        ('4001', 'Хлеб', 'White Bread', 50, 30, 30, 'Bakery'),
        ('4002', 'Круассан', 'Croissant', 75, 45, 20, 'Bakery'),
        ('4003', 'Торт', 'Chocolate Cake', 350, 220, 10, 'Bakery'),
        ('4004', 'Батон', 'Sliced Loaf', 55, 35, 25, 'Bakery'),
        ('4005', 'Пирожное', 'Cake Slice', 120, 70, 15, 'Bakery'),
        ('5001', 'Шоколад', 'Chocolate', 120, 80, 40, 'Sweets'),
        ('5002', 'Конфеты', 'Candies', 200, 140, 25, 'Sweets'),
        ('5003', 'Мороженое', 'Ice Cream', 95, 60, 15, 'Sweets'),
        ('5004', 'Печенье', 'Cookies', 110, 70, 30, 'Sweets'),
        ('5005', 'Мармелад', 'Marmalade', 85, 55, 20, 'Sweets'),
        ('6001', 'Курица', 'Chicken Fillet', 450, 320, 20, 'Meat & Fish'),
        ('6002', 'Говядина', 'Beef', 650, 480, 15, 'Meat & Fish'),
        ('6003', 'Рыба', 'Fish Fillet', 350, 250, 10, 'Meat & Fish'),
        ('6004', 'Колбаса', 'Cooked Sausage', 280, 200, 18, 'Meat & Fish'),
        ('6005', 'Фарш', 'Minced Meat', 320, 230, 12, 'Meat & Fish'),
        ('7001', 'Яблоки', 'Apples', 150, 100, 30, 'Fruits & Vegetables'),
        ('7002', 'Бананы', 'Bananas', 120, 80, 25, 'Fruits & Vegetables'),
        ('7003', 'Картофель', 'Potatoes', 80, 50, 40, 'Fruits & Vegetables'),
        ('7004', 'Помидоры', 'Tomatoes', 180, 120, 20, 'Fruits & Vegetables'),
        ('7005', 'Огурцы', 'Cucumbers', 140, 90, 18, 'Fruits & Vegetables'),
        ('8001', 'Стиральный порошок', 'Laundry Detergent', 350, 250, 15, 'Household'),
        ('8002', 'Мыло', 'Liquid Soap', 150, 100, 20, 'Household'),
        ('8003', 'Шампунь', 'Shampoo', 250, 180, 12, 'Household'),
        ('8004', 'Средство для посуды', 'Dish Soap', 120, 80, 25, 'Household'),
        ('8005', 'Освежитель', 'Air Freshener', 180, 130, 10, 'Household'),
        ('9001', 'Наушники', 'Headphones', 1500, 1000, 8, 'Electronics'),
        ('9002', 'USB кабель', 'USB Cable', 300, 200, 15, 'Electronics'),
        ('9003', 'Зарядка', 'Charger', 500, 350, 10, 'Electronics'),
        ('9004', 'Карта памяти', 'Memory Card', 800, 600, 6, 'Electronics'),
        ('9005', 'Флешка', 'Flash Drive', 400, 280, 12, 'Electronics'),
        ('10001', 'Футболка', 'T-Shirt', 800, 500, 15, 'Clothing'),
        ('10002', 'Джинсы', 'Jeans', 2500, 1800, 8, 'Clothing'),
        ('10003', 'Носки', 'Socks', 150, 100, 30, 'Clothing'),
        ('10004', 'Шапка', 'Winter Hat', 600, 400, 10, 'Clothing'),
        ('10005', 'Шарф', 'Scarf', 450, 300, 12, 'Clothing'),
        ('11001', 'Крем', 'Hand Cream', 250, 180, 20, 'Cosmetics'),
        ('11002', 'Помада', 'Lipstick', 400, 280, 15, 'Cosmetics'),
        ('11003', 'Тушь', 'Mascara', 350, 240, 10, 'Cosmetics'),
        ('11004', 'Тональный крем', 'Foundation', 500, 350, 8, 'Cosmetics'),
        ('11005', 'Лак', 'Nail Polish', 180, 120, 25, 'Cosmetics'),
        ('12001', 'Батарейки', 'AA Batteries', 200, 140, 20, 'Other'),
        ('12002', 'Лампочка', 'LED Bulb', 250, 180, 12, 'Other'),
        ('12003', 'Свечи', 'Candles', 350, 250, 8, 'Other'),
        ('12004', 'Скотч', 'Tape', 80, 50, 30, 'Other'),
        ('12005', 'Ножницы', 'Scissors', 180, 120, 10, 'Other'),
    ]
    
    for p in products:
        c.execute('SELECT id FROM categories WHERE name_en = ?', (p[6],))
        cat = c.fetchone()
        if cat:
            c.execute('INSERT INTO products (barcode, name_ru, name_en, price, cost, quantity, category_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
                      (p[0], p[1], p[2], p[3], p[4], p[5], cat[0]))
    
    conn.commit()
    conn.close()
    
    # Verify
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM products')
    prod_count = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM categories')
    cat_count = c.fetchone()[0]
    conn.close()
    
    print(f"✅ Database ready! Categories: {cat_count}, Products: {prod_count}")

# Initialize database on startup
if not os.path.exists(DB_NAME):
    init_db()
else:
    # Verify data exists
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM products')
        count = c.fetchone()[0]
        conn.close()
        if count == 0:
            init_db()
        else:
            print(f"✅ Database already exists with {count} products")
    except:
        init_db()

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ========== ROUTES ==========

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        password = request.form.get('password')
        try:
            conn = get_db()
            c = conn.cursor()
            c.execute('SELECT * FROM employees WHERE employee_id = ? AND password = ?', (employee_id, password))
            user = c.fetchone()
            conn.close()
            if user:
                session['user_id'] = user['employee_id']
                session['user_name'] = user['name']
                session['user_role'] = user['role']
                return jsonify({'status': 'success', 'role': user['role']})
            return jsonify({'status': 'error', 'message': 'Invalid credentials!'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

def login_required(f):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/')
@login_required
def index():
    return render_template('index.html', user=session)

@app.route('/api/products')
@login_required
def get_products():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM products ORDER BY id DESC')
    products = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(products)

@app.route('/api/categories')
@login_required
def get_categories():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM categories ORDER BY name_en')
    categories = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(categories)

@app.route('/api/stats')
@login_required
def get_stats():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) as count FROM products')
    total_products = c.fetchone()['count']
    c.execute('SELECT COUNT(*) as count FROM sales')
    total_sales = c.fetchone()['count']
    conn.close()
    return jsonify({
        'total_products': total_products,
        'total_sales': total_sales,
        'today_sales': 0,
        'low_stock': 0
    })

@app.route('/api/products_with_category')
@login_required
def get_products_with_category():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT p.*, c.name_ru as category_ru, c.name_en as category_en, 
               c.icon as category_icon, c.color as category_color
        FROM products p LEFT JOIN categories c ON p.category_id = c.id
        ORDER BY p.id DESC
    ''')
    products = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(products)

@app.route('/api/category_stats')
@login_required
def get_category_stats():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT c.id, c.name_ru, c.name_en, c.icon, c.color, COUNT(p.id) as product_count
        FROM categories c LEFT JOIN products p ON c.id = p.category_id
        GROUP BY c.id ORDER BY c.name_en
    ''')
    stats = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(stats)

@app.route('/api/verify_admin', methods=['POST'])
def verify_admin():
    data = request.json
    password = data.get('password', '')
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM employees WHERE employee_id = "ADMIN001" AND password = ?', (password,))
    user = c.fetchone()
    conn.close()
    if user:
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Invalid admin password!'})

# ========== START APP ==========
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)