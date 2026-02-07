# app.py (Updated: Add/Delete Customer, Payments)

from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from datetime import datetime
import os
from flask_mail import Mail, Message
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure secret key

# ------------------------
# MySQL Database Connection
# ------------------------
db = mysql.connector.connect(
    host="localhost",
    user="Enter your username",
    password="Enter your password",
    database="mydb"
)
cursor = db.cursor(dictionary=True)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="Enter your username",
        password="Enter your password",
        database="mydb"
    )

def update_sql_file(operation, table_name, data):
    """Update the SQL file with new data"""
    try:
        # Get the absolute path to the database.sql file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sql_file = os.path.join(current_dir, "database.sql")
        
        # Check if file exists
        if not os.path.exists(sql_file):
            print(f"Error: {sql_file} not found")
            return
        
        # Read the current SQL file
        with open(sql_file, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Find the INSERT statement for the table
        insert_start = content.find(f"INSERT INTO {table_name}")
        if insert_start == -1:
            print(f"Error: Could not find INSERT statement for table {table_name}")
            return
        
        # Find the end of the INSERT statement
        insert_end = content.find(";", insert_start)
        if insert_end == -1:
            print(f"Error: Could not find end of INSERT statement for table {table_name}")
            return
        
        # Extract the existing values
        existing_values = content[insert_start:insert_end]
        
        # Create new INSERT statement
        if operation == 'add':
            # Add new value to the existing values
            new_values = existing_values.rstrip(");") + f",\n{data});"
        elif operation == 'delete':
            # Remove the specified value
            # First try with newline
            if f",\n{data}" in existing_values:
                new_values = existing_values.replace(f",\n{data}", "")
            # Then try without newline
            elif f",{data}" in existing_values:
                new_values = existing_values.replace(f",{data}", "")
            # If it's the last item (no comma)
            elif f"{data});" in existing_values:
                new_values = existing_values.replace(f"{data});", ");")
            else:
                print(f"Warning: Could not find data to delete: {data}")
                new_values = existing_values
        
        # Replace the old INSERT statement with the new one
        updated_content = content[:insert_start] + new_values + content[insert_end + 1:]
        
        # Write back to the file
        with open(sql_file, 'w', encoding='utf-8') as file:
            file.write(updated_content)
            
        print(f"Successfully updated {sql_file} for {operation} operation on {table_name}")
        
    except Exception as e:
        print(f"Error updating SQL file: {str(e)}")

# ------------------------
# Logging Function
# ------------------------
def log_entity_change(operation, entity_type, entity_id, details):
    """Log entity changes to a file with proper formatting and error handling"""
    try:
        # Get current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Format the log entry with clear separation
        log_entry = f"[{timestamp}] {operation}: {entity_type} (ID: {entity_id})\n"
        log_entry += f"Details: {details}\n"
        log_entry += "-" * 80 + "\n"  # Add a separator line for readability
        
        # Get the absolute path to the logs directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        logs_dir = os.path.join(current_dir, "logs")
        
        # Create logs directory if it doesn't exist
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        
        # Write to the log file
        log_file = os.path.join(logs_dir, "entity_changes.log")
        with open(log_file, 'a', encoding='utf-8') as file:
            file.write(log_entry)
            
        print(f"Successfully logged {operation} operation for {entity_type} {entity_id}")
        
    except Exception as e:
        print(f"Error logging entity change: {str(e)}")
        # Don't raise the exception to prevent disrupting the main application flow

# ------------------------
# Helper Functions
# ------------------------
def get_customer_payment_info(cursor, customer_id):
    """Get payment information for a customer"""
    cursor.execute("""
        SELECT p.date, p.amount
        FROM payment p
        JOIN does d ON p.payment_id = d.p_id
        WHERE d.customer_id = %s
        ORDER BY p.date DESC
        LIMIT 1
    """, (customer_id,))
    return cursor.fetchone()

def send_payment_reminder_email(customer_email, customer_name, due_date, due_amount):
    """Send payment reminder email to customer"""
    try:
        msg = Message(
            'Payment Reminder',
            recipients=[customer_email]
        )
        msg.body = f"""
Dear {customer_name},

This is a reminder that you have a payment due on {due_date.strftime('%Y-%m-%d')}.
Amount due: ₹{due_amount}

Please make the payment before the due date to avoid any late fees.

Best regards,
Your Local Vendor System
"""
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def send_overdue_notification_email(customer_email, customer_name, due_date, due_amount, days_overdue):
    """Send overdue payment notification email to customer"""
    try:
        msg = Message(
            '⚠️ Payment Overdue Notice',
            recipients=[customer_email]
        )
        msg.body = f"""
Dear {customer_name},

This is an urgent notice that your payment of ₹{due_amount} is overdue.
Due Date: {due_date.strftime('%Y-%m-%d')}
Days Overdue: {days_overdue}

Please make the payment as soon as possible to avoid any additional late fees.

Best regards,
Your Local Vendor System
"""
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending overdue email: {str(e)}")
        return False

def check_and_create_notifications(cursor, customer_id):
    """Check for upcoming and overdue payments and create notifications"""
    try:
        # Get all due payments (both upcoming and overdue)
        cursor.execute("""
            SELECT due_date, due_amount 
            FROM due_payment 
            WHERE customer_id = %s
            ORDER BY due_date ASC
        """, (customer_id,))
        due_payments = cursor.fetchall()

        for due_date, due_amount in due_payments:
            # Calculate days overdue if payment is past due
            days_overdue = (datetime.now().date() - due_date).days if due_date < datetime.now().date() else 0
            
            # Generate unique notification ID
            notification_id = str(uuid.uuid4())
            
            # Create appropriate message based on payment status
            if days_overdue > 0:
                message = f"⚠️ Payment of ₹{due_amount} is overdue by {days_overdue} days (Due: {due_date.strftime('%Y-%m-%d')})"
            else:
                message = f"Payment of ₹{due_amount} is due on {due_date.strftime('%Y-%m-%d')}"
            
            # Check if notification already exists
            cursor.execute("""
                SELECT notification_id 
                FROM notifications 
                WHERE customer_id = %s AND due_date = %s AND message = %s
            """, (customer_id, due_date, message))
            
            if not cursor.fetchone():
                # Insert new notification
                cursor.execute("""
                    INSERT INTO notifications (notification_id, customer_id, message, due_date)
                    VALUES (%s, %s, %s, %s)
                """, (notification_id, customer_id, message, due_date))
                
                # Get customer email
                cursor.execute("""
                    SELECT c2.Email, c.Name
                    FROM customer c
                    JOIN customer2 c2 ON c.Customer_id = c2.Customer_id
                    WHERE c.Customer_id = %s
                """, (customer_id,))
                result = cursor.fetchone()
                
                if result:
                    customer_email, customer_name = result
                    # Send appropriate email notification
                    if days_overdue > 0:
                        send_overdue_notification_email(customer_email, customer_name, due_date, due_amount, days_overdue)
                    else:
                        send_payment_reminder_email(customer_email, customer_name, due_date, due_amount)
                    
        return True
    except Exception as e:
        print(f"Error creating notifications: {str(e)}")
        return False

def update_all_customer_notifications():
    """Update notifications for all customers"""
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Get all customers
        cursor.execute("SELECT Customer_id FROM customer")
        customers = cursor.fetchall()
        
        for customer in customers:
            check_and_create_notifications(cursor, customer['customer_id'])
        
        db.commit()
        cursor.close()
        db.close()
        return True
    except Exception as e:
        print(f"Error updating notifications: {str(e)}")
        return False

# ------------------------
# Routes
# ------------------------

@app.route('/')
def index():
    return render_template("login.html")

@app.route('/vendor_register', methods=['GET', 'POST'])
def vendor_register():
    if request.method == 'POST':
        # Get form data
        vendor_id = request.form['vendor_id']
        name = request.form['name']
        email = request.form['email']
        mobile_no = request.form['mobile_no']
        state = request.form['state']
        city = request.form['city']
        town = request.form['town']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Get product data
        product_names = request.form.getlist('product_name')
        product_prices = request.form.getlist('product_price')
        
        # Validate passwords match
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('vendor_register.html')
        
        # Get database connection
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        try:
            # Check if vendor_id already exists
            cursor.execute("SELECT * FROM vendor WHERE vendor_id = %s", (vendor_id,))
            if cursor.fetchone():
                flash('Vendor ID already exists! Please choose a different ID.', 'error')
                return render_template('vendor_register.html')
            
            # Check if email already exists
            cursor.execute("SELECT * FROM vendor WHERE email = %s", (email,))
            if cursor.fetchone():
                flash('Email already registered! Please use a different email.', 'error')
                return render_template('vendor_register.html')
            
            # Get or create location
            cursor.execute("""
                SELECT location_id FROM location 
                WHERE state = %s AND city = %s AND town = %s
            """, (state, city, town))
            location = cursor.fetchone()
            
            if location:
                location_id = location['location_id']
            else:
                # Insert new location
                cursor.execute("""
                    INSERT INTO location (state, city, town)
                    VALUES (%s, %s, %s)
                """, (state, city, town))
                location_id = cursor.lastrowid
            
            # Hash the password
            hashed_password = generate_password_hash(password)
            
            # Insert new vendor
            cursor.execute("""
                INSERT INTO vendor (vendor_id, name, email, mobile_no, location_id, password)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (vendor_id, name, email, mobile_no, location_id, hashed_password))
            
            # Insert products if provided
            if product_names and product_prices:
                for index, (product_name, product_price) in enumerate(zip(product_names, product_prices)):
                    if product_name.strip() and product_price.strip():
                        try:
                            product_id = f"P{vendor_id[1:]}_{index+1}"
                            cursor.execute("""
                                INSERT INTO product (product_id, name, price, vendor_id)
                                VALUES (%s, %s, %s, %s)
                            """, (product_id, product_name, float(product_price), vendor_id))
                        except:
                            pass
            
            db.commit()
            flash('Registration successful! You can now login.', 'success')
            return redirect(url_for('vendor_login'))
            
        except mysql.connector.Error as err:
            db.rollback()
            flash(f'Registration failed: {str(err)}', 'error')
            return render_template('vendor_register.html')
        finally:
            cursor.close()
            db.close()
    
    return render_template('vendor_register.html')

@app.route('/vendor_login', methods=['GET', 'POST'])
def vendor_login():
    if request.method == 'POST':
        vendor_id = request.form['vendor_id']
        password = request.form['password']

        # Get database connection
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM vendor WHERE vendor_id = %s", (vendor_id,))
        vendor = cursor.fetchone()
        
        cursor.close()
        db.close()

        if vendor:
            # Check if vendor has a password set
            if vendor['password']:
                # Verify password with hash
                if check_password_hash(vendor['password'], password):
                    session.clear()
                    session['vendor_id'] = vendor['vendor_id']
                    session['user_type'] = 'vendor'
                    return redirect(url_for('vendor_dashboard'))
                else:
                    return render_template('vendor_login.html', error="Invalid Vendor ID or Password")
            else:
                # Legacy vendor without password - check if password matches name
                if password == vendor['name']:
                    session.clear()
                    session['vendor_id'] = vendor['vendor_id']
                    session['user_type'] = 'vendor'
                    return redirect(url_for('vendor_dashboard'))
                else:
                    return render_template('vendor_login.html', error="Invalid Vendor ID or Password")
        else:
            return render_template('vendor_login.html', error="Invalid Vendor ID or Password")

    return render_template('vendor_login.html')

@app.route('/vendor_dashboard')
def vendor_dashboard():
    if 'vendor_id' not in session or session.get('user_type') != 'vendor':
        return redirect(url_for('index'))
    
    # Get a fresh database connection
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    vendor_id = session['vendor_id']
    
    # Fetch fresh vendor data with location info
    cursor.execute("""
        SELECT v.*, l.city, l.state, l.town 
        FROM vendor v
        LEFT JOIN location l ON v.location_id = l.location_id
        WHERE v.vendor_id = %s
    """, (vendor_id,))
    vendor = cursor.fetchone()

    # Fetch fresh products data
    cursor.execute("SELECT * FROM product WHERE vendor_id = %s", (vendor_id,))
    products = cursor.fetchall()

    # Fetch fresh customers data with location info
    cursor.execute("""
        SELECT c.*, l.city, l.state, l.town 
        FROM customer c
        LEFT JOIN location l ON c.location_id = l.location_id
        WHERE c.vendor_id = %s
    """, (vendor_id,))
    customers = cursor.fetchall()

    customer_products = {}
    due_amounts = {}
    payment_dates = {}

    # Fetch fresh customer products, due amounts, and payment dates
    for customer in customers:
        cid = customer['customer_id']

        cursor.execute("""
            SELECT p.name, p.price
            FROM purchase
            JOIN product p ON purchase.product_id = p.product_id
            WHERE purchase.customer_id = %s
        """, (cid,))
        items = cursor.fetchall()
        customer_products[cid] = items

        cursor.execute("""
            SELECT SUM(d.amount) as total_due
            FROM does
            JOIN due_payment d ON does.p_id = d.payment_id
            WHERE does.customer_id = %s
        """, (cid,))
        due = cursor.fetchone()
        due_amounts[cid] = due['total_due'] if due['total_due'] else 0

        # Get payment date
        payment_info = get_customer_payment_info(cursor, cid)
        payment_dates[cid] = payment_info['date'] if payment_info else None

    # Close the connection
    cursor.close()
    db.close()

    return render_template("vendor_home.html",
                         vendor=vendor,
                         products=products,
                         customers=customers,
                         customer_products=customer_products,
                         due_amounts=due_amounts,
                         payment_dates=payment_dates)

@app.route('/vendor_home/<vendor_id>')
def vendor_home(vendor_id):
    # Get database connection
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    # Fetch vendor details with location info
    cursor.execute("""
        SELECT v.*, l.city, l.state, l.town 
        FROM vendor v
        LEFT JOIN location l ON v.location_id = l.location_id
        WHERE v.vendor_id = %s
    """, (vendor_id,))
    vendor = cursor.fetchone()
    
    # Fetch products sold by the vendor
    cursor.execute("SELECT * FROM product WHERE vendor_id = %s", (vendor_id,))
    products = cursor.fetchall()
    
    # Fetch customers linked to the vendor with location info
    cursor.execute("""
        SELECT c.*, l.city, l.state, l.town 
        FROM customer c
        LEFT JOIN location l ON c.location_id = l.location_id
        WHERE c.vendor_id = %s
    """, (vendor_id,))
    customers = cursor.fetchall()
    
    # Fetch customer products and due amounts
    customer_products = {}
    due_amounts = {}
    payment_dates = {}
    
    for customer in customers:
        customer_id = customer['customer_id']
        
        # Get products purchased by this customer
        cursor.execute("""
            SELECT p.* FROM product p
            JOIN purchase b ON p.product_id = b.product_id
            WHERE b.customer_id = %s
        """, (customer_id,))
        customer_products[customer_id] = cursor.fetchall()
        
        # Get due payment amount for this customer
        cursor.execute("""
            SELECT SUM(dp.amount) as total_due
            FROM does d
            JOIN due_payment dp ON d.p_id = dp.payment_id
            WHERE d.customer_id = %s
        """, (customer_id,))
        due_result = cursor.fetchone()
        due_amounts[customer_id] = due_result['total_due'] if due_result['total_due'] else 0
        
        # Get payment date for this customer
        cursor.execute("""
            SELECT dp.due_date AS date
            FROM does d
            JOIN due_payment dp ON d.p_id = dp.payment_id
            WHERE d.customer_id = %s
            ORDER BY dp.due_date DESC
            LIMIT 1
        """, (customer_id,))
        date_result = cursor.fetchone()
        payment_dates[customer_id] = date_result['date'] if date_result else None
    
    # Close the connection
    cursor.close()
    db.close()
    
    return render_template("vendor_home.html",
                         vendor=vendor,
                         products=products,
                         customers=customers,
                         customer_products=customer_products,
                         due_amounts=due_amounts,
                         payment_dates=payment_dates)

@app.route('/customer_login', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        customer_id = request.form['customer_id']

        # Get database connection
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Check if customer exists
        cursor.execute("SELECT * FROM customer WHERE customer_id = %s", (customer_id,))
        customer = cursor.fetchone()
        
        # Close the connection
        cursor.close()
        db.close()

        if customer:
            session['customer_id'] = customer_id
            session['user_type'] = 'customer'
            return redirect(url_for('customer_dashboard'))
        else:
            return render_template('customer_login.html', error="Invalid Customer ID")

    return render_template('customer_login.html')

@app.route('/customer_dashboard')
def customer_dashboard():
    if 'customer_id' not in session or session.get('user_type') != 'customer':
        return redirect(url_for('index'))
    
    # Get a fresh database connection
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    customer_id = session['customer_id']
    
    # First check if customer still exists with location info
    cursor.execute("""
        SELECT c.*, l.city, l.state, l.town 
        FROM customer c
        LEFT JOIN location l ON c.location_id = l.location_id
        WHERE c.customer_id = %s
    """, (customer_id,))
    customer = cursor.fetchone()
    
    if not customer:
        # If customer doesn't exist, clear session and redirect to login
        session.clear()
        return redirect(url_for('customer_login'))
    
    # Check and create notifications
    check_and_create_notifications(cursor, customer_id)
    
    # Fetch notifications
    cursor.execute("""
        SELECT * FROM notifications 
        WHERE customer_id = %s 
        ORDER BY created_at DESC
    """, (customer_id,))
    notifications = cursor.fetchall()
    
    # Fetch fresh purchases data
    cursor.execute("""
        SELECT p.name, p.price
        FROM purchase
        JOIN product p ON purchase.product_id = p.product_id
        WHERE purchase.customer_id = %s
    """, (customer_id,))
    purchases = cursor.fetchall()

    # Fetch fresh due payment data
    cursor.execute("""
        SELECT SUM(d.amount) AS total_due, MAX(d.due_date) AS max_due_date
        FROM does
        JOIN due_payment d ON does.p_id = d.payment_id
        WHERE does.customer_id = %s
    """, (customer_id,))
    due_data = cursor.fetchone()
    
    # Fetch purchase date
    cursor.execute("""
        SELECT MAX(p.date) AS purchase_date
        FROM does
        JOIN payment p ON does.p_id = p.payment_id
        WHERE does.customer_id = %s
    """, (customer_id,))
    purchase_data = cursor.fetchone()

    # Close the connection
    cursor.close()
    db.close()

    return render_template("customer_dashboard.html",
                         customer=customer,
                         purchases=purchases,
                         due_amount=due_data['total_due'] or 0,
                         due_date=due_data['max_due_date'],
                         purchase_date=purchase_data['purchase_date'] if purchase_data else None,
                         notifications=notifications)

@app.route('/logout')
def logout():
    user_type = session.get('user_type')
    session.clear()
    if user_type == 'vendor':
        return redirect(url_for('vendor_login'))
    elif user_type == 'customer':
        return redirect(url_for('customer_login'))
    return redirect(url_for('index'))

@app.route('/add_customer/<vendor_id>', methods=['GET', 'POST'])
def add_customer(vendor_id):
    # Get database connection and fetch products first
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM product WHERE vendor_id = %s", (vendor_id,))
    products = cursor.fetchall()
    cursor.close()
    db.close()

    if request.method == 'POST':
        try:
            # Get database connection
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)
            
            customer_id = request.form['Customer_id']
            name = request.form['Name']
            dob = request.form['DOB']
            city = request.form['City']
            town = request.form['Town']
            state = request.form['State']
            
            # Get or create location
            cursor.execute("""
                SELECT location_id FROM location 
                WHERE state = %s AND city = %s AND town = %s
            """, (state, city, town))
            location = cursor.fetchone()
            
            if location:
                location_id = location['location_id']
            else:
                # Insert new location
                cursor.execute("""
                    INSERT INTO location (state, city, town)
                    VALUES (%s, %s, %s)
                """, (state, city, town))
                location_id = cursor.lastrowid
            
            # Insert customer data
            cursor.execute("""
                INSERT INTO customer (customer_id, name, dob, location_id, vendor_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (customer_id, name, dob, location_id, vendor_id))

            # Generate a unique payment ID
            cursor.execute("SELECT MAX(CAST(SUBSTRING(payment_id, 2) AS UNSIGNED)) AS last_id FROM payment WHERE payment_id LIKE 'P%'")
            result = cursor.fetchone()
            last_id = result['last_id'] if result['last_id'] else 0
            new_payment_id = f"P{last_id + 1:03d}"

            # Insert payment data
            paid_amount = request.form['AmountPaid']
            due_amount = request.form['AmountDue']
            purchase_date = request.form['PurchaseDate']
            
            cursor.execute("""
                INSERT INTO payment (payment_id, customer_id, vendor_id, date, amount)
                VALUES (%s, %s, %s, %s, %s)
            """, (new_payment_id, customer_id, vendor_id, purchase_date, paid_amount))

            # Only insert due payment if there is a due amount
            if due_amount and float(due_amount) > 0:
                due_date = request.form['DueDate']
                due_payment_id = f"DP{last_id + 1:03d}"
                cursor.execute("""
                    INSERT INTO due_payment (due_payment_id, payment_id, due_date, amount)
                    VALUES (%s, %s, %s, %s)
                """, (due_payment_id, new_payment_id, due_date, due_amount))

                # Create notification for the due payment
                notification_id = str(uuid.uuid4())
                message = f"Payment of ₹{due_amount} is due on {due_date}"
                cursor.execute("""
                    INSERT INTO notifications (notification_id, customer_id, message, due_date)
                    VALUES (%s, %s, %s, %s)
                """, (notification_id, customer_id, message, due_date))

            # Link customer and payment (does table)
            cursor.execute("""
                INSERT INTO does (customer_id, p_id)
                VALUES (%s, %s)
            """, (customer_id, new_payment_id))

            # Insert purchased products
            selected_products = request.form.getlist('products')
            for product_id in selected_products:
                cursor.execute("""
                    INSERT INTO purchase (customer_id, product_id, payment_id)
                    VALUES (%s, %s, %s)
                """, (customer_id, product_id, new_payment_id))

            # Commit changes
            db.commit()
            
            # Close the connection
            cursor.close()
            db.close()
            
            # Clear any cached data
            session.pop('_flashes', None)
            
            # Stay on the current page
            return redirect(request.referrer or url_for('vendor_dashboard'))
            
        except Exception as e:
            print(f"Error adding customer: {str(e)}")
            if 'db' in locals():
                db.rollback()
                db.close()
            return render_template("add_customer.html", 
                                 vendor_id=vendor_id, 
                                 products=products,
                                 error="An error occurred while adding the customer.")

    # GET request - render the form with products
    return render_template("add_customer.html", vendor_id=vendor_id, products=products)

@app.route('/delete_customer/<vendor_id>/<customer_id>', methods=['POST'])
def delete_customer(vendor_id, customer_id):
    try:
        # Get database connection
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Temporarily disable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        # Get payment IDs for this customer
        cursor.execute("SELECT p_id FROM does WHERE customer_id = %s", (customer_id,))
        payment_ids = [row['p_id'] for row in cursor.fetchall()]
        
        # Delete notifications
        cursor.execute("DELETE FROM notifications WHERE customer_id = %s", (customer_id,))
        
        # Delete from does (customer-payment junction)
        cursor.execute("DELETE FROM does WHERE customer_id = %s", (customer_id,))
        
        # Delete from purchase
        cursor.execute("DELETE FROM purchase WHERE customer_id = %s", (customer_id,))
        
        # Delete from due_payment for this customer's payments
        if payment_ids:
            format_strings = ','.join(['%s'] * len(payment_ids))
            cursor.execute(f"DELETE FROM due_payment WHERE payment_id IN ({format_strings})", tuple(payment_ids))
        
        # Delete payments for this customer
        if payment_ids:
            format_strings = ','.join(['%s'] * len(payment_ids))
            cursor.execute(f"DELETE FROM payment WHERE payment_id IN ({format_strings})", tuple(payment_ids))
        
        # Get customer's location_id before deletion
        cursor.execute("SELECT location_id FROM customer WHERE customer_id = %s", (customer_id,))
        customer_row = cursor.fetchone()
        customer_location_id = customer_row['location_id'] if customer_row else None

        # Delete the customer
        cursor.execute("DELETE FROM customer WHERE customer_id = %s", (customer_id,))

        # Delete location if it's not used by any other vendor or customer
        if customer_location_id:
            cursor.execute("SELECT COUNT(*) as count FROM vendor WHERE location_id = %s", (customer_location_id,))
            vendor_count = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM customer WHERE location_id = %s", (customer_location_id,))
            customer_count = cursor.fetchone()['count']

            if vendor_count == 0 and customer_count == 0:
                cursor.execute("DELETE FROM location WHERE location_id = %s", (customer_location_id,))
        
        # Re-enable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        # Commit the transaction
        db.commit()
        
        # Close the connection
        cursor.close()
        db.close()
        
        # If the deleted customer is currently logged in, clear their session
        if session.get('customer_id') == customer_id:
            session.clear()
        
        # Return empty response to stay on the same page
        return '', 204
        
    except Exception as e:
        print(f"Error deleting customer: {str(e)}")
        import traceback
        traceback.print_exc()
        # Rollback the transaction in case of error
        if 'db' in locals():
            try:
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
                db.rollback()
            except:
                pass
            db.close()
        # Return error response
        return str(e), 500

@app.route('/mark_notification_read/<notification_id>', methods=['POST'])
def mark_notification_read(notification_id):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Update notification as read
        cursor.execute("""
            UPDATE notifications 
            SET is_read = TRUE 
            WHERE notification_id = %s
        """, (notification_id,))
        
        db.commit()
        cursor.close()
        db.close()
        
        return redirect(url_for('customer_dashboard'))
    except Exception as e:
        print(f"Error marking notification as read: {str(e)}")
        return redirect(url_for('customer_dashboard'))

# Add a route to manually trigger notification updates
@app.route('/update_notifications')
def update_notifications():
    if update_all_customer_notifications():
        flash('Notifications updated successfully', 'success')
    else:
        flash('Error updating notifications', 'error')
    return redirect(url_for('index'))

# ------------------------
# Delete Vendor Route
# ------------------------
@app.route('/delete_vendor/<vendor_id>', methods=['POST'])
def delete_vendor(vendor_id):
    db = None
    cursor = None
    try:
        # Security check: only allow vendor to delete their own account
        session_vendor_id = session.get('vendor_id')
        if not session_vendor_id or session_vendor_id.lower() != vendor_id.lower():
            return '', 403
        
        vendor_id_db = session_vendor_id
        
        # Get database connection
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        print(f"Attempting to delete vendor: {vendor_id}")
        
        # Temporarily disable foreign key checks for cascading deletes
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        print("Foreign key checks disabled")
        
        # Fetch all related IDs first (to avoid MySQL subquery issues)
        cursor.execute("SELECT customer_id FROM customer WHERE vendor_id = %s", (vendor_id_db,))
        customer_ids = [row['customer_id'] for row in cursor.fetchall()]
        print(f"Found {len(customer_ids)} customers: {customer_ids}")
        
        cursor.execute("SELECT product_id FROM product WHERE vendor_id = %s", (vendor_id_db,))
        product_ids = [row['product_id'] for row in cursor.fetchall()]
        print(f"Found {len(product_ids)} products: {product_ids}")
        
        cursor.execute("SELECT payment_id FROM payment WHERE vendor_id = %s", (vendor_id_db,))
        payment_ids = [row['payment_id'] for row in cursor.fetchall()]
        print(f"Found {len(payment_ids)} payments: {payment_ids}")
        
        # Get vendor's location_id before deletion
        cursor.execute("SELECT location_id FROM vendor WHERE vendor_id = %s", (vendor_id_db,))
        vendor_row = cursor.fetchone()
        vendor_location_id = vendor_row['location_id'] if vendor_row else None
        print(f"Vendor location_id: {vendor_location_id}")

        # Get customer location_ids before deletion
        cursor.execute("""
            SELECT DISTINCT location_id
            FROM customer
            WHERE vendor_id = %s AND location_id IS NOT NULL
        """, (vendor_id_db,))
        customer_location_ids = [row['location_id'] for row in cursor.fetchall()]
        print(f"Customer location_ids: {customer_location_ids}")
        
        # Delete notifications
        if customer_ids:
            placeholders = ','.join(['%s'] * len(customer_ids))
            cursor.execute(f"DELETE FROM notifications WHERE customer_id IN ({placeholders})", tuple(customer_ids))
            print(f"Deleted {cursor.rowcount} notifications")
        
        # Delete does
        if customer_ids:
            placeholders = ','.join(['%s'] * len(customer_ids))
            cursor.execute(f"DELETE FROM does WHERE customer_id IN ({placeholders})", tuple(customer_ids))
            print(f"Deleted {cursor.rowcount} does records")
        
        # Delete ALL purchase records
        all_ids = []
        queries = []
        if customer_ids:
            all_ids.extend(customer_ids)
            queries.append(f"customer_id IN ({','.join(['%s'] * len(customer_ids))})")
        if product_ids:
            all_ids.extend(product_ids)
            queries.append(f"product_id IN ({','.join(['%s'] * len(product_ids))})")
        if payment_ids:
            all_ids.extend(payment_ids)
            queries.append(f"payment_id IN ({','.join(['%s'] * len(payment_ids))})")
        
        if queries:
            delete_query = f"DELETE FROM purchase WHERE {' OR '.join(queries)}"
            cursor.execute(delete_query, tuple(all_ids))
            print(f"Deleted {cursor.rowcount} purchase records")
        
        # Delete due_payment
        if payment_ids:
            placeholders = ','.join(['%s'] * len(payment_ids))
            cursor.execute(f"DELETE FROM due_payment WHERE payment_id IN ({placeholders})", tuple(payment_ids))
            print(f"Deleted {cursor.rowcount} due_payment records")
        
        # Delete payments
        cursor.execute("DELETE FROM payment WHERE vendor_id = %s", (vendor_id_db,))
        print(f"Deleted {cursor.rowcount} payments")
        
        # Delete products
        cursor.execute("DELETE FROM product WHERE vendor_id = %s", (vendor_id_db,))
        print(f"Deleted {cursor.rowcount} products")
        
        # Delete customers
        cursor.execute("DELETE FROM customer WHERE vendor_id = %s", (vendor_id_db,))
        print(f"Deleted {cursor.rowcount} customers")
        
        # Delete the vendor
        cursor.execute("DELETE FROM vendor WHERE vendor_id = %s", (vendor_id_db,))
        print(f"Deleted {cursor.rowcount} vendor")
        
        # Delete vendor location if it's not being used by any other vendor or customer
        if vendor_location_id:
            cursor.execute("SELECT COUNT(*) as count FROM vendor WHERE location_id = %s", (vendor_location_id,))
            vendor_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM customer WHERE location_id = %s", (vendor_location_id,))
            customer_count = cursor.fetchone()['count']
            
            if vendor_count == 0 and customer_count == 0:
                cursor.execute("DELETE FROM location WHERE location_id = %s", (vendor_location_id,))
                print(f"Deleted location {vendor_location_id}")
            else:
                print(f"Location {vendor_location_id} still in use by {vendor_count} vendors and {customer_count} customers")

        # Delete customer locations if they're not used by any other vendor or customer
        for location_id in customer_location_ids:
            if vendor_location_id and location_id == vendor_location_id:
                continue
            cursor.execute("SELECT COUNT(*) as count FROM vendor WHERE location_id = %s", (location_id,))
            vendor_count = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM customer WHERE location_id = %s", (location_id,))
            customer_count = cursor.fetchone()['count']

            if vendor_count == 0 and customer_count == 0:
                cursor.execute("DELETE FROM location WHERE location_id = %s", (location_id,))
                print(f"Deleted customer location {location_id}")
        
        # Re-enable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        print("Foreign key checks re-enabled")
        
        # Commit the transaction
        db.commit()
        print("Transaction committed")
        
        # Close the connection
        cursor.close()
        db.close()
        
        # Clear the session since the vendor account is deleted
        session.clear()
        
        print(f"Successfully deleted vendor {vendor_id}")
        # Return success status code
        return '', 204
        
    except Exception as e:
        print(f"Error deleting vendor: {str(e)}")
        import traceback
        traceback.print_exc()
        # Rollback the transaction in case of error
        if db is not None:
            try:
                if cursor is not None:
                    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
                db.rollback()
                db.close()
            except Exception as rollback_error:
                print(f"Error during rollback: {rollback_error}")
        return '', 500

# ------------------------
# Run Flask App
# ------------------------
if __name__ == '__main__':
    app.run(debug=True)
