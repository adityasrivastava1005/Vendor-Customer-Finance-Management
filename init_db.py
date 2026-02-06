#!/usr/bin/env python
# init_db.py - Database initialization script

import mysql.connector
import os
import sys

def init_database():
    """
    Initialize the database by executing the SQL script
    """
    try:
        # Connect to MySQL server (without database)
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Aditya@100105"
        )
        cursor = conn.cursor()
        
        print("Connected to MySQL server")
        
        # Read the SQL script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sql_file = os.path.join(current_dir, "database.sql")
        
        if not os.path.exists(sql_file):
            print(f"Error: {sql_file} not found")
            return False
        
        with open(sql_file, 'r', encoding='utf-8') as file:
            sql_script = file.read()
        
        # Split the script into individual statements
        statements = sql_script.split(';')
        
        # Execute each statement
        for statement in statements:
            if statement.strip():
                try:
                    cursor.execute(statement)
                    conn.commit()
                except mysql.connector.Error as err:
                    print(f"Error executing statement: {err}")
                    print(f"Statement: {statement}")
        
        print("Database initialized successfully")
        
        # Test connection to the database
        cursor.execute("USE mydb")
        cursor.execute("SELECT COUNT(*) FROM customer")
        count = cursor.fetchone()[0]
        print(f"Found {count} customers in the database")
        
        cursor.execute("SELECT COUNT(*) FROM vendor")
        count = cursor.fetchone()[0]
        print(f"Found {count} vendors in the database")
        
        cursor.execute("SELECT COUNT(*) FROM product")
        count = cursor.fetchone()[0]
        print(f"Found {count} products in the database")
        
        cursor.close()
        conn.close()
        
        return True
        
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return False

def test_app_connection():
    """
    Test the connection from the Flask app to the database
    """
    try:
        # Import the get_db_connection function from app.py
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from app import get_db_connection
        
        # Get a connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Test a simple query
        cursor.execute("SELECT * FROM vendor LIMIT 1")
        vendor = cursor.fetchone()
        
        if vendor:
            print(f"Successfully connected to database from app.py")
            print(f"Test vendor: {vendor['name']} (ID: {vendor['vendor_id']})")
        else:
            print("Connected to database but no vendors found")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Error testing app connection: {e}")
        return False

if __name__ == "__main__":
    print("Initializing database...")
    if init_database():
        print("\nTesting app connection...")
        test_app_connection()
        print("\nDatabase initialization and testing complete!")
    else:
        print("\nDatabase initialization failed!") 