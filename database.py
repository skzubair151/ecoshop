import sqlite3

DB_NAME = 'ecoshop.db'

def init_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # ========== CREATE CATEGORIES TABLE ==========
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_ru TEXT,
            name_en TEXT,
            icon TEXT,
            color TEXT
        )
    ''')
    
    # ========== CREATE PRODUCTS TABLE ==========
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE,
            name_ru TEXT,
            name_en TEXT,
            price REAL,
            cost REAL,
            quantity INTEGER DEFAULT 0,
            category_id INTEGER,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')
    
    # ========== CREATE EMPLOYEES TABLE ==========
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT UNIQUE,
            name TEXT,
            password TEXT,
            role TEXT,
            status TEXT DEFAULT 'Active'
        )
    ''')
    
    # ========== CREATE SALES TABLE ==========
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT UNIQUE,
            employee_id TEXT,
            customer_name TEXT,
            sale_date DATETIME,
            total_amount REAL,
            discount REAL DEFAULT 0,
            payment_method TEXT
        )
    ''')
    
    # ========== CREATE SALE ITEMS TABLE ==========
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            price REAL,
            FOREIGN KEY (sale_id) REFERENCES sales(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    
    # ========== INSERT DEFAULT EMPLOYEE ==========
    cursor.execute('''
        INSERT OR IGNORE INTO employees (employee_id, name, password, role, status)
        VALUES ('ADMIN001', 'Admin', 'admin123', 'Admin', 'Active')
    ''')
    
    cursor.execute('''
        INSERT OR IGNORE INTO employees (employee_id, name, password, role, status)
        VALUES ('EMP001', 'Zubair', 'staff123', 'Staff', 'Active')
    ''')
    
    # ========== INSERT CATEGORIES ==========
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
    
    for cat in categories:
        cursor.execute('''
            INSERT OR IGNORE INTO categories (name_ru, name_en, icon, color)
            VALUES (?, ?, ?, ?)
        ''', cat)
    
    # ========== INSERT PRODUCTS ==========
    products = [
        # Dairy (5)
        ('1001', 'Молоко 1л', 'Milk 1L', 120, 80, 50, 'Dairy'),
        ('1002', 'Йогурт клубничный', 'Yogurt', 85, 55, 30, 'Dairy'),
        ('1003', 'Сыр 200г', 'Cheese', 250, 180, 20, 'Dairy'),
        ('1004', 'Сметана 200г', 'Sour Cream', 95, 65, 25, 'Dairy'),
        ('1005', 'Масло сливочное', 'Butter', 180, 130, 15, 'Dairy'),
        
        # Beverages (5)
        ('2001', 'Кока-Кола 1л', 'Coca-Cola', 150, 100, 40, 'Beverages'),
        ('2002', 'Вода минеральная', 'Mineral Water', 60, 35, 100, 'Beverages'),
        ('2003', 'Сок апельсиновый', 'Orange Juice', 200, 140, 25, 'Beverages'),
        ('2004', 'Чай черный', 'Black Tea', 120, 80, 30, 'Beverages'),
        ('2005', 'Кофе растворимый', 'Instant Coffee', 350, 250, 20, 'Beverages'),
        
        # Groceries (5)
        ('3001', 'Рис 1кг', 'Rice', 180, 120, 60, 'Groceries'),
        ('3002', 'Макароны 500г', 'Pasta', 90, 60, 45, 'Groceries'),
        ('3003', 'Масло подсолнечное', 'Sunflower Oil', 220, 160, 35, 'Groceries'),
        ('3004', 'Мука 1кг', 'Flour', 95, 65, 50, 'Groceries'),
        ('3005', 'Сахар 1кг', 'Sugar', 110, 75, 40, 'Groceries'),
        
        # Bakery (5)
        ('4001', 'Хлеб белый', 'White Bread', 50, 30, 30, 'Bakery'),
        ('4002', 'Круассан', 'Croissant', 75, 45, 20, 'Bakery'),
        ('4003', 'Торт шоколадный', 'Chocolate Cake', 350, 220, 10, 'Bakery'),
        ('4004', 'Батон нарезной', 'Sliced Loaf', 55, 35, 25, 'Bakery'),
        ('4005', 'Пирожное', 'Cake Slice', 120, 70, 15, 'Bakery'),
        
        # Sweets (5)
        ('5001', 'Шоколад', 'Chocolate', 120, 80, 40, 'Sweets'),
        ('5002', 'Конфеты', 'Candies', 200, 140, 25, 'Sweets'),
        ('5003', 'Мороженое', 'Ice Cream', 95, 60, 15, 'Sweets'),
        ('5004', 'Печенье 300г', 'Cookies', 110, 70, 30, 'Sweets'),
        ('5005', 'Мармелад', 'Marmalade', 85, 55, 20, 'Sweets'),
        
        # Meat & Fish (5)
        ('6001', 'Куриное филе', 'Chicken Fillet', 450, 320, 20, 'Meat & Fish'),
        ('6002', 'Говядина', 'Beef', 650, 480, 15, 'Meat & Fish'),
        ('6003', 'Филе рыбы', 'Fish Fillet', 350, 250, 10, 'Meat & Fish'),
        ('6004', 'Колбаса вареная', 'Cooked Sausage', 280, 200, 18, 'Meat & Fish'),
        ('6005', 'Фарш мясной', 'Minced Meat', 320, 230, 12, 'Meat & Fish'),
        
        # Fruits & Vegetables (5)
        ('7001', 'Яблоки 1кг', 'Apples', 150, 100, 30, 'Fruits & Vegetables'),
        ('7002', 'Бананы 1кг', 'Bananas', 120, 80, 25, 'Fruits & Vegetables'),
        ('7003', 'Картофель 1кг', 'Potatoes', 80, 50, 40, 'Fruits & Vegetables'),
        ('7004', 'Помидоры 1кг', 'Tomatoes', 180, 120, 20, 'Fruits & Vegetables'),
        ('7005', 'Огурцы 1кг', 'Cucumbers', 140, 90, 18, 'Fruits & Vegetables'),
        
        # Household (5)
        ('8001', 'Порошок стиральный', 'Laundry Detergent', 350, 250, 15, 'Household'),
        ('8002', 'Мыло жидкое', 'Liquid Soap', 150, 100, 20, 'Household'),
        ('8003', 'Шампунь', 'Shampoo', 250, 180, 12, 'Household'),
        ('8004', 'Средство для посуды', 'Dish Soap', 120, 80, 25, 'Household'),
        ('8005', 'Освежитель воздуха', 'Air Freshener', 180, 130, 10, 'Household'),
        
        # Electronics (5)
        ('9001', 'Наушники', 'Headphones', 1500, 1000, 8, 'Electronics'),
        ('9002', 'USB кабель', 'USB Cable', 300, 200, 15, 'Electronics'),
        ('9003', 'Зарядное устройство', 'Charger', 500, 350, 10, 'Electronics'),
        ('9004', 'Карта памяти 32GB', 'Memory Card', 800, 600, 6, 'Electronics'),
        ('9005', 'Флешка 16GB', 'Flash Drive', 400, 280, 12, 'Electronics'),
        
        # Clothing (5)
        ('10001', 'Футболка', 'T-Shirt', 800, 500, 15, 'Clothing'),
        ('10002', 'Джинсы', 'Jeans', 2500, 1800, 8, 'Clothing'),
        ('10003', 'Носки', 'Socks', 150, 100, 30, 'Clothing'),
        ('10004', 'Шапка', 'Winter Hat', 600, 400, 10, 'Clothing'),
        ('10005', 'Шарф', 'Scarf', 450, 300, 12, 'Clothing'),
        
        # Cosmetics (5)
        ('11001', 'Крем для рук', 'Hand Cream', 250, 180, 20, 'Cosmetics'),
        ('11002', 'Помада', 'Lipstick', 400, 280, 15, 'Cosmetics'),
        ('11003', 'Тушь', 'Mascara', 350, 240, 10, 'Cosmetics'),
        ('11004', 'Тональный крем', 'Foundation', 500, 350, 8, 'Cosmetics'),
        ('11005', 'Лак для ногтей', 'Nail Polish', 180, 120, 25, 'Cosmetics'),
        
        # Other (5)
        ('12001', 'Батарейки AA', 'AA Batteries', 200, 140, 20, 'Other'),
        ('12002', 'Лампочка LED', 'LED Bulb', 250, 180, 12, 'Other'),
        ('12003', 'Свечи', 'Candles', 350, 250, 8, 'Other'),
        ('12004', 'Скотч', 'Tape', 80, 50, 30, 'Other'),
        ('12005', 'Ножницы', 'Scissors', 180, 120, 10, 'Other'),
    ]
    
    for p in products:
        cursor.execute('SELECT id FROM categories WHERE name_en = ?', (p[6],))
        cat = cursor.fetchone()
        if cat:
            cursor.execute('''
                INSERT OR IGNORE INTO products 
                (barcode, name_ru, name_en, price, cost, quantity, category_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (p[0], p[1], p[2], p[3], p[4], p[5], cat[0]))
    
    conn.commit()
    conn.close()
    
    # ========== SHOW SUMMARY ==========
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM categories')
    cat_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM products')
    prod_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM employees')
    emp_count = cursor.fetchone()[0]
    conn.close()
    
    print("=" * 50)
    print("✅ ECOSHOP DATABASE READY!")
    print("=" * 50)
    print(f"📂 Categories: {cat_count}")
    print(f"📦 Products: {prod_count}")
    print(f"👤 Employees: {emp_count}")
    print("=" * 50)
    print("🔐 Admin Login: ADMIN001 / admin123")
    print("👤 Staff Login: EMP001 / staff123")
    print("=" * 50)
    print("🚀 Run: python app.py")
    print("=" * 50)

if __name__ == '__main__':
    init_database()