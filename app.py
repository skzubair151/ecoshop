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

@app.route('/')
def index():
    if 'user_id' in session:
        return render_template('index.html', user=session)
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        password = request.form.get('password')
        try:
            conn = get_db()
            c = conn.cursor()
            c.execute('SELECT * FROM employees WHERE employee_id = ? AND password = ? AND status = "Active"', (employee_id, password))
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

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('index.html', user=session)

# ========== PRODUCTS API ==========
@app.route('/api/products')
@login_required
def get_products():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM products ORDER BY id DESC')
    products = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(products)

@app.route('/api/products', methods=['POST'])
@login_required
def add_product():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    
    try:
        c.execute('INSERT INTO products (barcode, name_ru, name_en, price, cost, quantity, category_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
                  (data.get('barcode', ''), data.get('name_ru', ''), data.get('name_en', ''),
                   float(data.get('price', 0)), float(data.get('cost', 0)), int(data.get('quantity', 0)),
                   data.get('category_id') if data.get('category_id') else None))
        conn.commit()
        return jsonify({'status': 'success', 'message': 'Product added!'})
    except sqlite3.IntegrityError:
        return jsonify({'status': 'error', 'message': 'Barcode already exists!'})
    finally:
        conn.close()

@app.route('/api/products/<int:product_id>', methods=['PUT'])
@login_required
def update_product(product_id):
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE products SET barcode=?, name_ru=?, name_en=?, price=?, cost=?, quantity=?, category_id=? WHERE id=?',
              (data.get('barcode', ''), data.get('name_ru', ''), data.get('name_en', ''),
               float(data.get('price', 0)), float(data.get('cost', 0)), int(data.get('quantity', 0)),
               data.get('category_id') if data.get('category_id') else None, product_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Product updated!'})

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM products WHERE id=?', (product_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Product deleted!'})

# ========== CATEGORIES API ==========
@app.route('/api/categories')
@login_required
def get_categories():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM categories ORDER BY name_en')
    categories = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(categories)

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

@app.route('/api/stats')
@login_required
def get_stats():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) as count FROM products')
    total_products = c.fetchone()['count']
    c.execute('SELECT COUNT(*) as count FROM sales')
    total_sales = c.fetchone()['count']
    today = datetime.now().date().isoformat()
    c.execute('SELECT SUM(total_amount) as total FROM sales WHERE DATE(sale_date) = ?', (today,))
    result = c.fetchone()
    today_sales = result['total'] if result and result['total'] else 0
    c.execute('SELECT COUNT(*) as count FROM products WHERE quantity < 5')
    low_stock = c.fetchone()['count']
    conn.close()
    return jsonify({
        'total_products': total_products,
        'total_sales': total_sales,
        'today_sales': today_sales,
        'low_stock': low_stock
    })

# ========== SALES API ==========
@app.route('/api/sales', methods=['POST'])
@login_required
def create_sale():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    
    invoice_no = f"INV-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
    
    try:
        c.execute('''
            INSERT INTO sales (invoice_no, employee_id, customer_name, sale_date, total_amount, discount, payment_method)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            invoice_no,
            session.get('user_id'),
            data.get('customer_name', 'Walk-in Customer'),
            datetime.now().isoformat(),
            float(data.get('total_amount', 0)),
            float(data.get('discount', 0)),
            data.get('payment_method', 'cash')
        ))
        
        sale_id = c.lastrowid
        
        for item in data.get('items', []):
            c.execute('''
                INSERT INTO sale_items (sale_id, product_id, quantity, price)
                VALUES (?, ?, ?, ?)
            ''', (
                sale_id,
                item['product_id'],
                item['quantity'],
                item['price']
            ))
            
            c.execute('''
                UPDATE products SET quantity = quantity - ? 
                WHERE id = ? AND quantity >= ?
            ''', (item['quantity'], item['product_id'], item['quantity']))
        
        conn.commit()
        return jsonify({'status': 'success', 'invoice_no': invoice_no})
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)})
    finally:
        conn.close()

# ========== REPORTS API ==========
@app.route('/api/reports/sales')
@login_required
def get_sales_report():
    period = request.args.get('period', 'daily')
    conn = get_db()
    c = conn.cursor()
    
    today = datetime.now().date()
    if period == 'daily':
        start_date = today.isoformat()
        end_date = today.isoformat()
    elif period == 'weekly':
        start_date = (today - timedelta(days=7)).isoformat()
        end_date = today.isoformat()
    elif period == 'monthly':
        start_date = (today - timedelta(days=30)).isoformat()
        end_date = today.isoformat()
    else:
        start_date = (today - timedelta(days=365)).isoformat()
        end_date = today.isoformat()
    
    c.execute('''
        SELECT DATE(sale_date) as date, COUNT(*) as total_sales, SUM(total_amount) as total_revenue, 
        SUM(discount) as total_discount, AVG(total_amount) as average_sale
        FROM sales WHERE DATE(sale_date) BETWEEN ? AND ? GROUP BY DATE(sale_date) ORDER BY DATE(sale_date) DESC
    ''', (start_date, end_date))
    
    sales_data = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(sales_data)

@app.route('/api/reports/top_products')
@login_required
def get_top_products():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT p.id, p.barcode, p.name_ru, p.name_en, SUM(si.quantity) as total_sold, 
        SUM(si.quantity * si.price) as total_revenue, COUNT(DISTINCT si.sale_id) as order_count
        FROM sale_items si JOIN products p ON si.product_id = p.id GROUP BY si.product_id ORDER BY total_sold DESC LIMIT 10
    ''')
    products = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(products)

@app.route('/api/reports/low_stock')
@login_required
def get_low_stock():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT p.*, c.name_ru as category_ru, c.name_en as category_en
        FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE p.quantity < 5 ORDER BY p.quantity ASC
    ''')
    products = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(products)

@app.route('/api/reports/profit')
@login_required
def get_profit_report():
    period = request.args.get('period', 'daily')
    conn = get_db()
    c = conn.cursor()
    
    today = datetime.now().date()
    if period == 'daily':
        start_date = today.isoformat()
        end_date = today.isoformat()
    elif period == 'weekly':
        start_date = (today - timedelta(days=7)).isoformat()
        end_date = today.isoformat()
    elif period == 'monthly':
        start_date = (today - timedelta(days=30)).isoformat()
        end_date = today.isoformat()
    else:
        start_date = (today - timedelta(days=365)).isoformat()
        end_date = today.isoformat()
    
    c.execute('''
        SELECT SUM(si.quantity * si.price) as total_revenue, SUM(si.quantity * p.cost) as total_cost, 
        SUM(si.quantity * (si.price - p.cost)) as total_profit
        FROM sale_items si JOIN products p ON si.product_id = p.id JOIN sales s ON si.sale_id = s.id
        WHERE DATE(s.sale_date) BETWEEN ? AND ?
    ''', (start_date, end_date))
    
    result = c.fetchone()
    conn.close()
    return jsonify({
        'total_revenue': result['total_revenue'] if result and result['total_revenue'] else 0,
        'total_cost': result['total_cost'] if result and result['total_cost'] else 0,
        'total_profit': result['total_profit'] if result and result['total_profit'] else 0
    })

# ========== EMPLOYEE API ==========
@app.route('/api/employees')
@login_required
def get_employees():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM employees ORDER BY id')
    employees = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(employees)

@app.route('/api/employees', methods=['POST'])
@login_required
def add_employee():
    if session.get('user_role') != 'Admin':
        return jsonify({'status': 'error', 'message': 'Admin only!'})
    
    data = request.json
    conn = get_db()
    c = conn.cursor()
    
    try:
        c.execute('INSERT INTO employees (employee_id, name, password, role, status) VALUES (?, ?, ?, ?, ?)',
                  (data.get('employee_id', ''), data.get('name', ''), data.get('password', ''),
                   data.get('role', 'Staff'), data.get('status', 'Active')))
        conn.commit()
        return jsonify({'status': 'success', 'message': 'Employee added!'})
    except sqlite3.IntegrityError:
        return jsonify({'status': 'error', 'message': 'Employee ID already exists!'})
    finally:
        conn.close()

@app.route('/api/employees/<int:emp_id>', methods=['PUT'])
@login_required
def update_employee(emp_id):
    if session.get('user_role') != 'Admin':
        return jsonify({'status': 'error', 'message': 'Admin only!'})
    
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE employees SET name=?, password=?, role=?, status=? WHERE id=?',
              (data.get('name', ''), data.get('password', ''), data.get('role', 'Staff'),
               data.get('status', 'Active'), emp_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Employee updated!'})

@app.route('/api/employees/<int:emp_id>', methods=['DELETE'])
@login_required
def delete_employee(emp_id):
    if session.get('user_role') != 'Admin':
        return jsonify({'status': 'error', 'message': 'Admin only!'})
    
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM employees WHERE id=?', (emp_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Employee deleted!'})

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

# ========== EXPORT REPORTS ==========
@app.route('/api/reports/export')
@login_required
def export_report():
    period = request.args.get('period', 'daily')
    format_type = request.args.get('format', 'excel')
    
    conn = get_db()
    c = conn.cursor()
    
    today = datetime.now().date()
    if period == 'daily':
        start_date = today.isoformat()
        end_date = today.isoformat()
    elif period == 'weekly':
        start_date = (today - timedelta(days=7)).isoformat()
        end_date = today.isoformat()
    elif period == 'monthly':
        start_date = (today - timedelta(days=30)).isoformat()
        end_date = today.isoformat()
    else:
        start_date = (today - timedelta(days=365)).isoformat()
        end_date = today.isoformat()
    
    c.execute('''
        SELECT DATE(s.sale_date) as date, s.invoice_no, s.customer_name, 
        s.total_amount, s.discount, s.payment_method, e.name as employee_name
        FROM sales s LEFT JOIN employees e ON s.employee_id = e.employee_id
        WHERE DATE(s.sale_date) BETWEEN ? AND ? ORDER BY s.sale_date DESC
    ''', (start_date, end_date))
    
    data = [dict(row) for row in c.fetchall()]
    conn.close()
    
    if format_type == 'excel' or format_type == 'csv':
        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Date', 'Invoice', 'Customer', 'Total', 'Discount', 'Payment', 'Employee'])
        for row in data:
            writer.writerow([row['date'], row['invoice_no'], row['customer_name'], 
                           row['total_amount'], row['discount'], row['payment_method'], row['employee_name']])
        output.seek(0)
        from flask import send_file
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'sales_report_{period}.csv'
        )
    
    elif format_type == 'pdf':
        return jsonify({
            'status': 'success',
            'data': data,
            'message': 'PDF report generated'
        })
    
    else:
        return jsonify({'status': 'error', 'message': 'Unsupported format'})

# ========== START APP ==========
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)