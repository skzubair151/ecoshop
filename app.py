from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
import sqlite3
import os
from datetime import datetime, timedelta
import random
import csv
import io
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

app = Flask(__name__)
app.secret_key = 'ecoshop_secret_key_2026'

DB_NAME = 'ecoshop.db'

def init_db():
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
        c.execute('''
            INSERT INTO products (barcode, name_ru, name_en, price, cost, quantity, weight, unit_type, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('barcode', ''),
            data.get('name_ru', ''),
            data.get('name_en', ''),
            float(data.get('price', 0)),
            float(data.get('cost', 0)),
            float(data.get('quantity', 0)),
            float(data.get('weight', 0)),
            data.get('unit_type', 'qty'),
            data.get('category_id') if data.get('category_id') else None
        ))
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
    c.execute('''
        UPDATE products SET barcode=?, name_ru=?, name_en=?, price=?, cost=?, quantity=?, weight=?, unit_type=?, category_id=?
        WHERE id=?
    ''', (
        data.get('barcode', ''),
        data.get('name_ru', ''),
        data.get('name_en', ''),
        float(data.get('price', 0)),
        float(data.get('cost', 0)),
        float(data.get('quantity', 0)),
        float(data.get('weight', 0)),
        data.get('unit_type', 'qty'),
        data.get('category_id') if data.get('category_id') else None,
        product_id
    ))
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
        customer_discount = 0
        customer_id = data.get('customer_id')
        if customer_id:
            c.execute('SELECT discount_rate FROM customers WHERE customer_id = ?', (customer_id,))
            result = c.fetchone()
            if result:
                customer_discount = result['discount_rate']
        
        items = data.get('items', [])
        subtotal = 0
        for item in items:
            amount = item.get('quantity', 0) or item.get('weight', 0)
            subtotal += item['price'] * amount
        
        customer_discount_amount = subtotal * (customer_discount / 100)
        manual_discount = float(data.get('discount', 0))
        total_discount = customer_discount_amount + manual_discount
        total_amount = subtotal - total_discount
        
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
        
        for item in items:
            if item.get('unit_type') == 'weight':
                weight_sold = item.get('weight', 0)
                c.execute('UPDATE products SET weight = weight - ? WHERE id = ? AND weight >= ?', 
                         (weight_sold, item['product_id'], weight_sold))
                c.execute('''
                    INSERT INTO sale_items (sale_id, product_id, quantity, weight, unit_type, price)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (sale_id, item['product_id'], 0, weight_sold, 'weight', item['price']))
            else:
                qty_sold = item.get('quantity', 0)
                c.execute('UPDATE products SET quantity = quantity - ? WHERE id = ? AND quantity >= ?', 
                         (qty_sold, item['product_id'], qty_sold))
                c.execute('''
                    INSERT INTO sale_items (sale_id, product_id, quantity, weight, unit_type, price)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (sale_id, item['product_id'], qty_sold, 0, 'qty', item['price']))
        
        conn.commit()
        
        try:
            from backup import auto_backup
            auto_backup()
        except:
            pass
        
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
        FROM products p LEFT JOIN categories c ON p.category_id = c.id 
        WHERE (p.unit_type = 'qty' AND p.quantity < 5) OR (p.unit_type = 'weight' AND p.weight < 1)
        ORDER BY p.quantity ASC
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

# ========== BACKUP API ==========
@app.route('/api/backup/status')
@login_required
def get_backup_status():
    try:
        backup_dir = 'backups'
        backups = []
        
        if os.path.exists(backup_dir):
            for f in os.listdir(backup_dir):
                if f.startswith('ecoshop_backup_') and f.endswith('.db'):
                    path = os.path.join(backup_dir, f)
                    size = os.path.getsize(path)
                    modified = datetime.fromtimestamp(os.path.getmtime(path))
                    backups.append({
                        'name': f,
                        'size': size,
                        'date': modified.strftime('%Y-%m-%d %H:%M:%S')
                    })
        
        backups = sorted(backups, key=lambda x: x['date'], reverse=True)
        
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM products')
        products = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM sales')
        sales = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM customers')
        customers = c.fetchone()[0]
        conn.close()
        
        return jsonify({
            'status': 'success',
            'backups': backups[:10],
            'stats': {
                'products': products,
                'sales': sales,
                'customers': customers
            },
            'last_backup': backups[0]['date'] if backups else None
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/backup/create', methods=['POST'])
@login_required
def create_backup():
    try:
        from backup import auto_backup
        result = auto_backup()
        
        if result:
            return jsonify({
                'status': 'success',
                'message': 'Backup created and uploaded to Google Drive!',
                'backup_file': os.path.basename(result)
            })
        else:
            return jsonify({'status': 'error', 'message': 'Backup creation failed!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/backup/download')
@login_required
def download_backup():
    try:
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            return jsonify({'status': 'error', 'message': 'No backups found!'})
        
        backups = []
        for f in os.listdir(backup_dir):
            if f.startswith('ecoshop_backup_') and f.endswith('.db'):
                path = os.path.join(backup_dir, f)
                backups.append((os.path.getmtime(path), path, f))
        
        if not backups:
            return jsonify({'status': 'error', 'message': 'No backups found!'})
        
        backups.sort(reverse=True)
        latest_path = backups[0][1]
        latest_name = backups[0][2]
        
        return send_file(
            latest_path,
            as_attachment=True,
            download_name=latest_name,
            mimetype='application/octet-stream'
        )
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

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
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=16,
            alignment=1,
            spaceAfter=20
        )
        
        content = []
        
        title = Paragraph(f"📊 Sales Report - {period.upper()}", title_style)
        content.append(title)
        content.append(Spacer(1, 10))
        
        date_info = Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal'])
        content.append(date_info)
        content.append(Spacer(1, 10))
        
        total_sales = len(data)
        total_revenue = sum(row['total_amount'] for row in data if row['total_amount'])
        total_discount = sum(row['discount'] for row in data if row['discount'])
        
        summary_data = [
            ['Total Sales', 'Total Revenue', 'Total Discount', 'Avg Sale'],
            [
                str(total_sales),
                f"{total_revenue:.2f}",
                f"{total_discount:.2f}",
                f"{total_revenue/total_sales:.2f}" if total_sales > 0 else "0.00"
            ]
        ]
        summary_table = Table(summary_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        content.append(summary_table)
        content.append(Spacer(1, 20))
        
        if data:
            table_data = [
                ['Date', 'Invoice', 'Customer', 'Total', 'Discount', 'Payment', 'Employee']
            ]
            for row in data:
                table_data.append([
                    row['date'] or '',
                    row['invoice_no'] or '',
                    row['customer_name'] or 'Walk-in',
                    f"{row['total_amount']:.2f}" if row['total_amount'] else '0.00',
                    f"{row['discount']:.2f}" if row['discount'] else '0.00',
                    row['payment_method'] or '',
                    row['employee_name'] or ''
                ])
            
            sales_table = Table(table_data, colWidths=[0.8*inch, 1.2*inch, 1.5*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1.2*inch])
            sales_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black)
            ]))
            content.append(sales_table)
        else:
            no_data = Paragraph("No sales data available for this period.", styles['Normal'])
            content.append(no_data)
        
        content.append(Spacer(1, 20))
        footer = Paragraph(f"Generated by EcoShop | {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal'])
        content.append(footer)
        
        doc.build(content)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'sales_report_{period}.pdf'
        )
    
    else:
        return jsonify({'status': 'error', 'message': 'Unsupported format'})

# ========== START APP ==========
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)

    # ========== PRODUCT IMAGE UPLOAD ==========
@app.route('/api/products/<int:product_id>/image', methods=['POST'])
@login_required
def upload_product_image(product_id):
    try:
        if 'image' not in request.files:
            return jsonify({'status': 'error', 'message': 'No image provided'})
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No image selected'})
        
        # Save image
        filename = f'product_{product_id}.jpg'
        filepath = os.path.join('static', 'product_images', filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        file.save(filepath)
        
        return jsonify({'status': 'success', 'message': 'Image uploaded!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})