import sqlite3
import os

DB_NAME = 'ecoshop.db'

def init_database():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # ===== CREATE TABLES =====
    c.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_ru TEXT, name_en TEXT, icon TEXT, color TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE,
            name_ru TEXT,
            name_en TEXT,
            price REAL,
            cost REAL,
            quantity REAL DEFAULT 0,
            weight REAL DEFAULT 0,
            unit_type TEXT DEFAULT 'qty',
            image TEXT,
            category_id INTEGER
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT UNIQUE,
            name TEXT,
            password TEXT,
            role TEXT,
            status TEXT DEFAULT 'Active'
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT UNIQUE,
            name TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            discount_rate REAL DEFAULT 0,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT UNIQUE,
            employee_id TEXT,
            customer_id TEXT,
            customer_name TEXT,
            sale_date DATETIME,
            total_amount REAL,
            discount REAL DEFAULT 0,
            payment_method TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER,
            product_id INTEGER,
            quantity REAL DEFAULT 0,
            weight REAL DEFAULT 0,
            unit_type TEXT DEFAULT 'qty',
            price REAL
        )
    ''')
    
    # ===== INSERT EMPLOYEES =====
    c.execute('INSERT OR IGNORE INTO employees (employee_id, name, password, role) VALUES (?, ?, ?, ?)',
              ('ADMIN001', 'Admin', 'admin123', 'Admin'))
    c.execute('INSERT OR IGNORE INTO employees (employee_id, name, password, role) VALUES (?, ?, ?, ?)',
              ('EMP001', 'Zubair', 'staff123', 'Staff'))
    
    # ===== INSERT CATEGORIES =====
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
    c.executemany('INSERT OR IGNORE INTO categories (name_ru, name_en, icon, color) VALUES (?, ?, ?, ?)', categories)
    
    # ===== INSERT PRODUCTS =====
    products = [
        ('1001', 'Молоко 1л', 'Milk 1L', 120, 80, 50, 0, 'qty', 'Dairy'),
        ('1002', 'Йогурт', 'Yogurt', 85, 55, 30, 0, 'qty', 'Dairy'),
        ('1003', 'Сыр 200г', 'Cheese', 250, 180, 20, 0, 'qty', 'Dairy'),
        ('1004', 'Сметана', 'Sour Cream', 95, 65, 25, 0, 'qty', 'Dairy'),
        ('1005', 'Масло', 'Butter', 180, 130, 15, 0, 'qty', 'Dairy'),
        ('2001', 'Кока-Кола', 'Coca-Cola', 150, 100, 40, 0, 'qty', 'Beverages'),
        ('2002', 'Вода', 'Mineral Water', 60, 35, 100, 0, 'qty', 'Beverages'),
        ('2003', 'Сок', 'Orange Juice', 200, 140, 25, 0, 'qty', 'Beverages'),
        ('2004', 'Чай', 'Black Tea', 120, 80, 30, 0, 'qty', 'Beverages'),
        ('2005', 'Кофе', 'Instant Coffee', 350, 250, 20, 0, 'qty', 'Beverages'),
        ('3001', 'Рис 1кг', 'Rice', 180, 120, 0, 50, 'weight', 'Groceries'),
        ('3002', 'Макароны 500г', 'Pasta', 90, 60, 0, 45, 'weight', 'Groceries'),
        ('3003', 'Масло растительное', 'Sunflower Oil', 220, 160, 0, 35, 'weight', 'Groceries'),
        ('3004', 'Мука 1кг', 'Flour', 95, 65, 0, 50, 'weight', 'Groceries'),
        ('3005', 'Сахар 1кг', 'Sugar', 110, 75, 0, 40, 'weight', 'Groceries'),
        ('4001', 'Хлеб', 'White Bread', 50, 30, 30, 0, 'qty', 'Bakery'),
        ('4002', 'Круассан', 'Croissant', 75, 45, 20, 0, 'qty', 'Bakery'),
        ('4003', 'Торт', 'Chocolate Cake', 350, 220, 10, 0, 'qty', 'Bakery'),
        ('4004', 'Батон', 'Sliced Loaf', 55, 35, 25, 0, 'qty', 'Bakery'),
        ('4005', 'Пирожное', 'Cake Slice', 120, 70, 15, 0, 'qty', 'Bakery'),
        ('5001', 'Шоколад', 'Chocolate', 120, 80, 40, 0, 'qty', 'Sweets'),
        ('5002', 'Конфеты', 'Candies', 200, 140, 25, 0, 'qty', 'Sweets'),
        ('5003', 'Мороженое', 'Ice Cream', 95, 60, 15, 0, 'qty', 'Sweets'),
        ('5004', 'Печенье', 'Cookies', 110, 70, 30, 0, 'qty', 'Sweets'),
        ('5005', 'Мармелад', 'Marmalade', 85, 55, 20, 0, 'qty', 'Sweets'),
        ('6001', 'Курица', 'Chicken Fillet', 450, 320, 0, 20, 'weight', 'Meat & Fish'),
        ('6002', 'Говядина', 'Beef', 650, 480, 0, 15, 'weight', 'Meat & Fish'),
        ('6003', 'Рыба', 'Fish Fillet', 350, 250, 0, 10, 'weight', 'Meat & Fish'),
        ('6004', 'Колбаса', 'Cooked Sausage', 280, 200, 18, 0, 'qty', 'Meat & Fish'),
        ('6005', 'Фарш', 'Minced Meat', 320, 230, 0, 12, 'weight', 'Meat & Fish'),
        ('7001', 'Яблоки', 'Apples', 150, 100, 0, 30, 'weight', 'Fruits & Vegetables'),
        ('7002', 'Бананы', 'Bananas', 120, 80, 0, 25, 'weight', 'Fruits & Vegetables'),
        ('7003', 'Картофель', 'Potatoes', 80, 50, 0, 40, 'weight', 'Fruits & Vegetables'),
        ('7004', 'Помидоры', 'Tomatoes', 180, 120, 0, 20, 'weight', 'Fruits & Vegetables'),
        ('7005', 'Огурцы', 'Cucumbers', 140, 90, 0, 18, 'weight', 'Fruits & Vegetables'),
        ('8001', 'Стиральный порошок', 'Laundry Detergent', 350, 250, 15, 0, 'qty', 'Household'),
        ('8002', 'Мыло', 'Liquid Soap', 150, 100, 20, 0, 'qty', 'Household'),
        ('8003', 'Шампунь', 'Shampoo', 250, 180, 12, 0, 'qty', 'Household'),
        ('8004', 'Средство для посуды', 'Dish Soap', 120, 80, 25, 0, 'qty', 'Household'),
        ('8005', 'Освежитель', 'Air Freshener', 180, 130, 10, 0, 'qty', 'Household'),
        ('9001', 'Наушники', 'Headphones', 1500, 1000, 8, 0, 'qty', 'Electronics'),
        ('9002', 'USB кабель', 'USB Cable', 300, 200, 15, 0, 'qty', 'Electronics'),
        ('9003', 'Зарядка', 'Charger', 500, 350, 10, 0, 'qty', 'Electronics'),
        ('9004', 'Карта памяти', 'Memory Card', 800, 600, 6, 0, 'qty', 'Electronics'),
        ('9005', 'Флешка', 'Flash Drive', 400, 280, 12, 0, 'qty', 'Electronics'),
        ('10001', 'Футболка', 'T-Shirt', 800, 500, 15, 0, 'qty', 'Clothing'),
        ('10002', 'Джинсы', 'Jeans', 2500, 1800, 8, 0, 'qty', 'Clothing'),
        ('10003', 'Носки', 'Socks', 150, 100, 30, 0, 'qty', 'Clothing'),
        ('10004', 'Шапка', 'Winter Hat', 600, 400, 10, 0, 'qty', 'Clothing'),
        ('10005', 'Шарф', 'Scarf', 450, 300, 12, 0, 'qty', 'Clothing'),
        ('11001', 'Крем', 'Hand Cream', 250, 180, 20, 0, 'qty', 'Cosmetics'),
        ('11002', 'Помада', 'Lipstick', 400, 280, 15, 0, 'qty', 'Cosmetics'),
        ('11003', 'Тушь', 'Mascara', 350, 240, 10, 0, 'qty', 'Cosmetics'),
        ('11004', 'Тональный крем', 'Foundation', 500, 350, 8, 0, 'qty', 'Cosmetics'),
        ('11005', 'Лак', 'Nail Polish', 180, 120, 25, 0, 'qty', 'Cosmetics'),
        ('12001', 'Батарейки', 'AA Batteries', 200, 140, 20, 0, 'qty', 'Other'),
        ('12002', 'Лампочка', 'LED Bulb', 250, 180, 12, 0, 'qty', 'Other'),
        ('12003', 'Свечи', 'Candles', 350, 250, 8, 0, 'qty', 'Other'),
        ('12004', 'Скотч', 'Tape', 80, 50, 30, 0, 'qty', 'Other'),
        ('12005', 'Ножницы', 'Scissors', 180, 120, 10, 0, 'qty', 'Other'),
    ]
    
    for p in products:
        c.execute('SELECT id FROM categories WHERE name_en = ?', (p[8],))
        cat = c.fetchone()
        if cat:
            c.execute('''
                INSERT OR IGNORE INTO products 
                (barcode, name_ru, name_en, price, cost, quantity, weight, unit_type, category_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], cat[0]))
    
    conn.commit()
    conn.close()
    
    # ===== VERIFY =====
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM products')
    prod_count = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM categories')
    cat_count = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM employees')
    emp_count = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM customers')
    cust_count = c.fetchone()[0]
    conn.close()
    
    print("=" * 50)
    print("✅ ECOSHOP DATABASE READY!")
    print("=" * 50)
    print(f"📂 Categories: {cat_count}")
    print(f"📦 Products: {prod_count}")
    print(f"👤 Employees: {emp_count}")
    print(f"👥 Customers: {cust_count}")
    print("=" * 50)
    print("🔐 Admin: ADMIN001 / admin123")
    print("👤 Staff: EMP001 / staff123")
    print("=" * 50)

if __name__ == '__main__':
    init_database()