# app.py (Updated: Add/Delete Customer, Payments)

from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from datetime import datetime
import os
from flask_mail import Mail, Message
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure secret key

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'ruthlessgamma538@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'qkwpylokyoclymiz'  # Replace with your app password
app.config['MAIL_DEFAULT_SENDER'] = 'ruthlessgamma538@gmail.com'  # Replace with your email

mail = Mail(app)

# ------------------------
# MySQL Database Connection
# ------------------------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="MANABsingh@29",
    database="project1"
)
cursor = db.cursor(dictionary=True)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="MANABsingh@29",
        database="project1"
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
        JOIN does d ON p.p_id = d.p_id
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
            check_and_create_notifications(cursor, customer['Customer_id'])
        
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

@app.route('/vendor_login', methods=['GET', 'POST'])
def vendor_login():
    if request.method == 'POST':
        vendor_id = request.form['vendor_id']
        name = request.form['name']

        cursor.execute("SELECT * FROM vendor WHERE vendor_id = %s AND name = %s", (vendor_id, name))
        vendor = cursor.fetchone()

        if vendor:
            session['vendor_id'] = vendor_id
            session['user_type'] = 'vendor'
            return redirect(url_for('vendor_dashboard'))
        else:
            return render_template('vendor_login.html', error="Invalid Vendor ID or Name")

    return render_template('vendor_login.html')

@app.route('/vendor_dashboard')
def vendor_dashboard():
    if 'vendor_id' not in session or session.get('user_type') != 'vendor':
        return redirect(url_for('index'))
    
    # Get a fresh database connection
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    vendor_id = session['vendor_id']
    
    # Fetch fresh vendor data
    cursor.execute("SELECT * FROM vendor WHERE vendor_id = %s", (vendor_id,))
    vendor = cursor.fetchone()

    # Fetch fresh products data
    cursor.execute("SELECT * FROM product WHERE vendor_id = %s", (vendor_id,))
    products = cursor.fetchall()

    # Fetch fresh customers data
    cursor.execute("SELECT * FROM customer WHERE vendor_id = %s", (vendor_id,))
    customers = cursor.fetchall()

    customer_products = {}
    due_amounts = {}
    payment_dates = {}

    # Fetch fresh customer products, due amounts, and payment dates
    for customer in customers:
        cid = customer['Customer_id']

        cursor.execute("""
            SELECT p.name, p.price
            FROM buy
            JOIN product p ON buy.product_id = p.product_id
            WHERE buy.customer_id = %s
        """, (cid,))
        items = cursor.fetchall()
        customer_products[cid] = items

        cursor.execute("""
            SELECT SUM(d.amount) as total_due
            FROM does
            JOIN due_payment d ON does.p_id = d.p_id
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
    
    # Fetch vendor details
    cursor.execute("SELECT * FROM vendor WHERE vendor_id = %s", (vendor_id,))
    vendor = cursor.fetchone()
    
    # Fetch products sold by the vendor
    cursor.execute("SELECT * FROM product WHERE vendor_id = %s", (vendor_id,))
    products = cursor.fetchall()
    
    # Fetch customers linked to the vendor
    cursor.execute("SELECT * FROM customer WHERE Vendor_id = %s", (vendor_id,))
    customers = cursor.fetchall()
    
    # Fetch customer products and due amounts
    customer_products = {}
    due_amounts = {}
    payment_dates = {}
    
    for customer in customers:
        customer_id = customer['Customer_id']
        
        # Get products purchased by this customer
        cursor.execute("""
            SELECT p.* FROM product p
            JOIN buy b ON p.product_id = b.product_id
            WHERE b.customer_id = %s
        """, (customer_id,))
        customer_products[customer_id] = cursor.fetchall()
        
        # Get due payment amount for this customer
        cursor.execute("""
            SELECT SUM(dp.amount) as total_due
            FROM does d
            JOIN due_payment dp ON d.p_id = dp.p_id
            WHERE d.customer_id = %s
        """, (customer_id,))
        due_result = cursor.fetchone()
        due_amounts[customer_id] = due_result['total_due'] if due_result['total_due'] else 0
        
        # Get payment date for this customer
        cursor.execute("""
            SELECT dp.date
            FROM does d
            JOIN due_payment dp ON d.p_id = dp.p_id
            WHERE d.customer_id = %s
            ORDER BY dp.date DESC
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
        cursor.execute("SELECT * FROM customer WHERE Customer_id = %s", (customer_id,))
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
    
    # First check if customer still exists
    cursor.execute("SELECT * FROM customer WHERE Customer_id = %s", (customer_id,))
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
        FROM buy
        JOIN product p ON buy.product_id = p.product_id
        WHERE buy.customer_id = %s
    """, (customer_id,))
    purchases = cursor.fetchall()

    # Fetch fresh due payment data
    cursor.execute("""
        SELECT SUM(d.amount) AS total_due, MAX(d.date) AS max_due_date
        FROM does
        JOIN due_payment d ON does.p_id = d.p_id
        WHERE does.customer_id = %s
    """, (customer_id,))
    due_data = cursor.fetchone()
    
    # Fetch purchase date
    cursor.execute("""
        SELECT MAX(p.date) AS purchase_date
        FROM does
        JOIN payment p ON does.p_id = p.p_id
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
            
            # Insert customer data
            customer_data = (
                request.form['Customer_id'],
                request.form['Name'],
                request.form['DOB'],
                request.form['Age'],
                request.form['City'],
                request.form['Town'],
                request.form['State'],
                vendor_id
            )
            cursor.execute("""
                INSERT INTO customer (Customer_id, Name, DOB, Age, City, Town, State, Vendor_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, customer_data)

            # Log the customer addition
            log_entity_change(
                "ADDED",
                "Customer",
                customer_data[0],
                f"Name: {customer_data[1]}, Location: {customer_data[4]}, {customer_data[5]}, {customer_data[6]}"
            )

            # Update SQL file for customer
            customer_sql = f"('{customer_data[0]}', '{customer_data[1]}', '{customer_data[2]}', {customer_data[3]}, '{customer_data[4]}', '{customer_data[5]}', '{customer_data[6]}', '{customer_data[7]}')"
            update_sql_file('add', 'customer', customer_sql)

            # Generate a unique payment ID
            cursor.execute("SELECT MAX(p_id) AS last_p_id FROM payment")
            last_p_id = cursor.fetchone()['last_p_id']
            if last_p_id:
                new_payment_id = f"P{int(last_p_id[1:]) + 1:03d}"
            else:
                new_payment_id = "P001"

            # Insert payment data
            paid_amount = request.form['AmountPaid']
            due_amount = request.form['AmountDue']
            purchase_date = request.form['PurchaseDate']
            
            cursor.execute("""
                INSERT INTO payment (p_id, date, amount, vendor_id)
                VALUES (%s, %s, %s, %s)
            """, (new_payment_id, purchase_date, paid_amount, vendor_id))

            # Update SQL file for payment
            payment_sql = f"('{new_payment_id}', '{purchase_date}', {paid_amount}, '{vendor_id}')"
            update_sql_file('add', 'payment', payment_sql)

            # Only insert due payment if there is a due amount
            if due_amount and int(due_amount) > 0:
                due_date = request.form['DueDate']
                cursor.execute("""
                    INSERT INTO due_payment (dueP_id, p_id, date, amount)
                    VALUES (%s, %s, %s, %s)
                """, (f'DP{new_payment_id[1:]}', new_payment_id, due_date, due_amount))

                # Update SQL file for due payment
                due_payment_sql = f"('DP{new_payment_id[1:]}', '{new_payment_id}', '{due_date}', {due_amount})"
                update_sql_file('add', 'due_payment', due_payment_sql)

                # Create notification for the due payment
                notification_id = str(uuid.uuid4())
                message = f"Payment of ₹{due_amount} is due on {due_date}"
                cursor.execute("""
                    INSERT INTO notifications (notification_id, customer_id, message, due_date)
                    VALUES (%s, %s, %s, %s)
                """, (notification_id, customer_data[0], message, due_date))

                # Send email notification if email is provided
                if 'Email' in request.form and request.form['Email']:
                    try:
                        send_payment_reminder_email(
                            request.form['Email'],
                            request.form['Name'],
                            datetime.strptime(due_date, '%Y-%m-%d').date(),
                            float(due_amount)
                        )
                    except Exception as e:
                        print(f"Error sending email notification: {str(e)}")

            # Link customer and payment
            customer_id = request.form['Customer_id']
            cursor.execute("""
                INSERT INTO does (customer_id, p_id)
                VALUES (%s, %s)
            """, (customer_id, new_payment_id))

            # Update SQL file for does
            does_sql = f"('{customer_id}', '{new_payment_id}')"
            update_sql_file('add', 'does', does_sql)

            # Insert purchased products
            selected_products = request.form.getlist('products')
            for product_id in selected_products:
                cursor.execute("""
                    INSERT INTO buy (customer_id, product_id)
                    VALUES (%s, %s)
                """, (customer_id, product_id))

                # Update SQL file for buy
                buy_sql = f"('{customer_id}', '{product_id}')"
                update_sql_file('add', 'buy', buy_sql)

            # Commit changes
            db.commit()
            
            # Close the connection
            cursor.close()
            db.close()
            
            # Clear any cached data
            session.pop('_flashes', None)
            
            # If the added customer is currently logged in, update their session
            if session.get('customer_id') == customer_id:
                session['customer_id'] = customer_id
                session['user_type'] = 'customer'
            
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
        
        # Delete notifications related to the customer
        cursor.execute("DELETE FROM notifications WHERE customer_id = %s", (customer_id,))
        
        # Get customer data before deletion for SQL file update
        cursor.execute("SELECT * FROM customer WHERE Customer_id = %s", (customer_id,))
        customer = cursor.fetchone()
        if customer:
            customer_sql = f"('{customer['Customer_id']}', '{customer['Name']}', '{customer['DOB']}', {customer['Age']}, '{customer['City']}', '{customer['Town']}', '{customer['State']}', '{customer['Vendor_id']}')"
            update_sql_file('delete', 'customer', customer_sql)

        # Get payment data before deletion
        cursor.execute("SELECT p_id FROM does WHERE customer_id = %s", (customer_id,))
        payments = cursor.fetchall()
        for payment in payments:
            cursor.execute("SELECT * FROM payment WHERE p_id = %s", (payment['p_id'],))
            payment_data = cursor.fetchone()
            if payment_data:
                payment_sql = f"('{payment_data['p_id']}', '{payment_data['date']}', {payment_data['amount']}, '{payment_data['vendor_id']}')"
                update_sql_file('delete', 'payment', payment_sql)

            cursor.execute("SELECT * FROM due_payment WHERE p_id = %s", (payment['p_id'],))
            due_payment_data = cursor.fetchone()
            if due_payment_data:
                due_payment_sql = f"('{due_payment_data['dueP_id']}', '{due_payment_data['p_id']}', '{due_payment_data['date']}', {due_payment_data['amount']})"
                update_sql_file('delete', 'due_payment', due_payment_sql)

            does_sql = f"('{customer_id}', '{payment['p_id']}')"
            update_sql_file('delete', 'does', does_sql)

        # Get buy data before deletion
        cursor.execute("SELECT * FROM buy WHERE customer_id = %s", (customer_id,))
        buys = cursor.fetchall()
        for buy in buys:
            buy_sql = f"('{buy['customer_id']}', '{buy['product_id']}')"
            update_sql_file('delete', 'buy', buy_sql)

        # Delete from database in the correct order (respecting foreign key constraints)
        # First delete from child tables
        cursor.execute("DELETE FROM does WHERE customer_id = %s", (customer_id,))
        cursor.execute("DELETE FROM buy WHERE customer_id = %s", (customer_id,))
        # Then delete from parent table
        cursor.execute("DELETE FROM customer WHERE Customer_id = %s", (customer_id,))
        
        # Commit the transaction
        db.commit()
        
        # Close the connection
        cursor.close()
        db.close()
        
        # If the deleted customer is currently logged in, just clear their session
        if session.get('customer_id') == customer_id:
            session.clear()
        
        # Return empty response to stay on the same page
        return '', 204
        
    except Exception as e:
        print(f"Error deleting customer: {str(e)}")
        # Rollback the transaction in case of error
        if 'db' in locals():
            db.rollback()
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
# Run Flask App
# ------------------------
if __name__ == '__main__':
    app.run(debug=True)
