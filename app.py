from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
import sqlite3
import os
from datetime import datetime, timedelta
import random
import csv
import io

app = Flask(__name__)
app.secret_key = 'ecoshop_secret_key_2026'

DB_NAME = 'ecoshop.db'

def init_db():
    """Initialize database with all data"""
    if not os.path.exists(DB_NAME):
        print("🔄 Creating database...")
        from database import init_database
        init_database()
    else:
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM products')
            count = c.fetchone()[0]
            conn.close()
            if count == 0:
                from database import init_database
                init_database()
            else:
                try:
                    conn = sqlite3.connect(DB_NAME)
                    c = conn.cursor()
                    c.execute('SELECT COUNT(*) FROM customers')
                    conn.close()
                except:
                    from database import init_database
                    init_database()
                print(f"✅ Database ready with {count} products")
        except:
            from database import init_database
            init_database()

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

# ========== CUSTOMER API ==========
@app.route('/api/customers')
@login_required
def get_customers():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM customers ORDER BY id DESC')
    customers = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(customers)

@app.route('/api/customers', methods=['POST'])
@login_required
def add_customer():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    
    try:
        c.execute('''
            INSERT INTO customers (customer_id, name, phone, email, address, discount_rate)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data.get('customer_id', ''),
            data.get('name', ''),
            data.get('phone', ''),
            data.get('email', ''),
            data.get('address', ''),
            float(data.get('discount_rate', 0))
        ))
        conn.commit()
        return jsonify({'status': 'success', 'message': 'Customer added!'})
    except sqlite3.IntegrityError:
        return jsonify({'status': 'error', 'message': 'Customer ID already exists!'})
    finally:
        conn.close()

@app.route('/api/customers/<int:customer_id>', methods=['PUT'])
@login_required
def update_customer(customer_id):
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        UPDATE customers SET name=?, phone=?, email=?, address=?, discount_rate=?
        WHERE id=?
    ''', (
        data.get('name', ''),
        data.get('phone', ''),
        data.get('email', ''),
        data.get('address', ''),
        float(data.get('discount_rate', 0)),
        customer_id
    ))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Customer updated!'})

@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
@login_required
def delete_customer(customer_id):
    if session.get('user_role') != 'Admin':
        return jsonify({'status': 'error', 'message': 'Admin only!'})
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM customers WHERE id=?', (customer_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Customer deleted!'})

@app.route('/api/customers/search')
@login_required
def search_customer():
    query = request.args.get('q', '')
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT * FROM customers 
        WHERE customer_id LIKE ? OR name LIKE ? OR phone LIKE ?
        LIMIT 10
    ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
    customers = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(customers)

# ========== SALES API ==========
@app.route('/api/sales', methods=['POST'])
@login_required
def create_sale():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    
    invoice_no = f"INV-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
    
    try:
        # Get customer discount if customer_id provided
        customer_discount = 0
        customer_id = data.get('customer_id')
        if customer_id:
            c.execute('SELECT discount_rate FROM customers WHERE customer_id = ?', (customer_id,))
            result = c.fetchone()
            if result:
                customer_discount = result['discount_rate']
        
        # Calculate total with customer discount
        items = data.get('items', [])
        subtotal = sum(item['price'] * item['quantity'] for item in items)
        customer_discount_amount = subtotal * (customer_discount / 100)
        manual_discount = float(data.get('discount', 0))
        total_discount = customer_discount_amount + manual_discount
        total_amount = subtotal - total_discount
        
        # Insert sale
        c.execute('''
            INSERT INTO sales (invoice_no, employee_id, customer_id, customer_name, 
                               sale_date, total_amount, discount, payment_method)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            invoice_no,
            session.get('user_id'),
            data.get('customer_id'),
            data.get('customer_name', 'Walk-in Customer'),
            datetime.now().isoformat(),
            total_amount,
            total_discount,
            data.get('payment_method', 'cash')
        ))
        
        sale_id = c.lastrowid
        
        # Insert sale items and update stock
        for item in items:
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
        return jsonify({
            'status': 'success',
            'invoice_no': invoice_no,
            'subtotal': subtotal,
            'customer_discount': customer_discount_amount,
            'manual_discount': manual_discount,
            'total_discount': total_discount,
            'total': total_amount
        })
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
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Date', 'Invoice', 'Customer', 'Total', 'Discount', 'Payment', 'Employee'])
        for row in data:
            writer.writerow([row['date'], row['invoice_no'], row['customer_name'], 
                           row['total_amount'], row['discount'], row['payment_method'], row['employee_name']])
        output.seek(0)
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