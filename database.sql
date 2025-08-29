-- Create Database
DROP DATABASE IF EXISTS project1;
CREATE DATABASE project1;
USE project1;

-- LOCATION Table (Normalized from redundant location data)
CREATE TABLE location (
    location_id INT AUTO_INCREMENT PRIMARY KEY,
    state VARCHAR(50) NOT NULL,
    city VARCHAR(50) NOT NULL,
    town VARCHAR(50) NOT NULL,
    UNIQUE KEY location_unique (state, city, town)
);

-- VENDOR Table (Normalized)
CREATE TABLE vendor (
    vendor_id VARCHAR(50) NOT NULL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    email VARCHAR(100),
    mobile_no VARCHAR(20),
    location_id INT,
    password VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES location(location_id)
);

-- CUSTOMER Table (Normalized)
CREATE TABLE customer (
    customer_id VARCHAR(50) NOT NULL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    dob DATE NOT NULL,
    email VARCHAR(100),
    mobile_no VARCHAR(20),
    location_id INT,
    vendor_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES location(location_id),
    FOREIGN KEY (vendor_id) REFERENCES vendor(vendor_id)
);

-- PRODUCT Table (Normalized)
CREATE TABLE product (
    product_id VARCHAR(50) NOT NULL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    vendor_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES vendor(vendor_id)
);

-- PAYMENT Table (Normalized)
CREATE TABLE payment (
    payment_id VARCHAR(50) NOT NULL PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    vendor_id VARCHAR(50) NOT NULL,
    date DATETIME NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id),
    FOREIGN KEY (vendor_id) REFERENCES vendor(vendor_id)
);

-- DUE_PAYMENT Table (Normalized)
CREATE TABLE due_payment (
    due_payment_id VARCHAR(50) NOT NULL PRIMARY KEY,
    payment_id VARCHAR(50) NOT NULL,
    due_date DATE NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (payment_id) REFERENCES payment(payment_id)
);

-- PURCHASE Table (Normalized from BUY table)
CREATE TABLE purchase (
    purchase_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    payment_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id),
    FOREIGN KEY (product_id) REFERENCES product(product_id),
    FOREIGN KEY (payment_id) REFERENCES payment(payment_id)
);

-- NOTIFICATIONS Table (Normalized)
CREATE TABLE notifications (
    notification_id VARCHAR(50) NOT NULL PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    due_date DATE,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
);

-- Insert sample data for location
INSERT INTO location (state, city, town) VALUES
('Maharashtra', 'Mumbai', 'Bandra'),
('Delhi', 'Delhi', 'Dwarka'),
('West Bengal', 'Kolkata', 'Salt Lake'),
('Tamil Nadu', 'Chennai', 'Adyar'),
('Maharashtra', 'Pune', 'Kothrud'),
('Gujarat', 'Ahmedabad', 'Navrangpura'),
('Karnataka', 'Bangalore', 'Indiranagar'),
('Telangana', 'Hyderabad', 'Banjara Hills'),
('Rajasthan', 'Jaipur', 'Malviya Nagar'),
('Uttar Pradesh', 'Lucknow', 'Hazratganj'),
('West Bengal', 'Kolkata', 'Taratala'),
('Uttar Pradesh', 'Ghaziabad', 'Noida'),
('Uttar Pradesh', 'Lucknow', 'Gomti Nagar'),
('Maharashtra', 'Mumbai', 'Andheri'),
('Tamil Nadu', 'Chennai', 'T Nagar'),
('Karnataka', 'Bengaluru', 'Whitefield'),
('West Bengal', 'Kolkata', 'Salt Lake'),
('Rajasthan', 'Jaipur', 'Malviya Nagar'),
('Punjab', 'Amritsar', 'Ranjit Avenue'),
('Gujarat', 'Ahmedabad', 'Satellite'),
('Madhya Pradesh', 'Bhopal', 'Arera Colony'),
('Kerala', 'Kochi', 'Fort Kochi'),
('Uttar Pradesh', 'Banaras', 'Chowk');

-- Insert sample data for vendor
INSERT INTO vendor (vendor_id, name, email, mobile_no, location_id) VALUES
('V001', 'Vendor One', 'vendor1@example.com', '9876543210', 13),
('V002', 'Vendor Two', 'vendor2@example.com', '9123456789', 14),
('V003', 'Vendor Three', 'vendor3@example.com', '8765432190', 15),
('V004', 'Vendor Four', 'vendor4@example.com', '7890123456', 16),
('V005', 'Vendor Five', 'vendor5@example.com', '6789012345', 17),
('V006', 'Vendor Six', 'vendor6@example.com', '5678901234', 18),
('V007', 'Vendor Seven', 'vendor7@example.com', '4567890123', 19),
('V008', 'Vendor Eight', 'vendor8@example.com', '3456789012', 20),
('V009', 'Vendor Nine', 'vendor9@example.com', '2345678901', 21),
('V010', 'Vendor Ten', 'vendor10@example.com', '1234567890', 22);

-- Insert sample data for customer
INSERT INTO customer (customer_id, name, dob, email, mobile_no, location_id, vendor_id) VALUES
('C001', 'John Doe', '1990-01-15', 'john.doe@example.com', '9876543210', 1, 'V001'),
('C002', 'Jane Smith', '1985-07-20', 'jane.smith@example.com', '9123456789', 2, 'V002'),
('C003', 'Ali Khan', '1992-03-10', 'ali.khan@example.com', '8765432190', 3, 'V003'),
('C004', 'Emily Davis', '1995-12-01', 'emily.davis@example.com', '7890123456', 4, 'V004'),
('C005', 'Rahul Sharma', '1988-05-25', 'rahul.sharma@example.com', '6789012345', 5, 'V005'),
('C006', 'Sanya Mehta', '1993-08-17', 'sanya.mehta@example.com', '5678901234', 6, 'V006'),
('C007', 'Arjun Verma', '1990-11-30', 'arjun.verma@example.com', '4567890123', 7, 'V007'),
('C008', 'Fatima Sheikh', '1996-09-18', 'fatima.sheikh@example.com', '3456789012', 8, 'V008'),
('C009', 'Chris Wong', '1987-02-14', 'chris.wong@example.com', '2345678901', 9, 'V009'),
('C010', 'Priya Kapoor', '1994-04-05', 'priya.kapoor@example.com', '1234567890', 10, 'V010'),
('C011', 'Matt Murdock', '2000-08-29', 'matt.murdock@example.com', '9876543211', 11, 'V001'),
('C017', 'Foggy', '2005-08-29', 'foggy@example.com', '9876543212', 12, 'V003',
('c098', 'khjabfk', '2003-08-29', 21, 'as', 'afs', 'af', 'V001'))

-- Insert sample data for product
INSERT INTO product (product_id, name, price, vendor_id) VALUES
('P001', 'Laptop', 50000.00, 'V001'),
('P002', 'Smartphone', 30000.00, 'V002'),
('P003', 'Tablet', 20000.00, 'V003'),
('P004', 'Smartwatch', 15000.00, 'V004'),
('P005', 'Desktop', 45000.00, 'V005'),
('P006', 'Gaming Console', 40000.00, 'V006'),
('P007', 'Headphones', 5000.00, 'V007'),
('P008', 'Keyboard', 2000.00, 'V008'),
('P009', 'Mouse', 1500.00, 'V009'),
('P010', 'Monitor', 12000.00, 'V010'),
('P022', 'Laptop Pro', 49600.00, 'V001'),
('P023', 'Tablet Pro', 19500.00, 'V003')

-- Insert sample data for payment
INSERT INTO payment (payment_id, customer_id, vendor_id, date, amount) VALUES
('P001', 'C001', 'V001', '2025-03-31 10:00:00', 1000.00),
('P002', 'C002', 'V002', '2025-03-30 11:15:00', 2000.00),
('P003', 'C003', 'V003', '2025-03-29 14:45:00', 1500.00),
('P004', 'C004', 'V004', '2025-03-28 09:00:00', 1200.00),
('P005', 'C005', 'V005', '2025-03-27 18:20:00', 1800.00),
('P006', 'C006', 'V006', '2025-03-26 12:30:00', 1100.00),
('P007', 'C007', 'V007', '2025-03-25 14:50:00', 1700.00),
('P008', 'C008', 'V008', '2025-03-24 11:10:00', 900.00),
('P009', 'C009', 'V009', '2025-03-23 15:40:00', 1400.00),
('P010', 'C010', 'V010', '2025-03-22 13:25:00', 1300.00),
('P022', 'C011', 'V001', '2025-04-20 10:07:05', 49600.00),
('P023', 'C017', 'V003', '2025-04-20 10:09:31', 19500.00,
('P045', '2025-04-22', 49000, 'V001'))

-- Insert sample data for due_payment
INSERT INTO due_payment (due_payment_id, payment_id, due_date, amount) VALUES
('DP001', 'P001', '2025-03-31', 500.00),
('DP002', 'P002', '2025-03-30', 1000.00),
('DP003', 'P003', '2025-03-29', 750.00),
('DP004', 'P004', '2025-03-28', 1200.00),
('DP005', 'P005', '2025-03-27', 300.00),
('DP006', 'P006', '2025-03-26', 450.00),
('DP007', 'P007', '2025-03-25', 600.00),
('DP008', 'P008', '2025-03-24', 850.00),
('DP009', 'P009', '2025-03-23', 700.00),
('DP010', 'P010', '2025-03-22', 900.00),
('DP022', 'P022', '2025-04-20', 400.00),
('DP023', 'P023', '2025-04-20', 500.00,
('DP045', 'P045', '2025-04-24', 1000))

-- Insert sample data for purchase
INSERT INTO purchase (customer_id, product_id, payment_id) VALUES
('C001', 'P001', 'P001'),
('C002', 'P002', 'P002'),
('C003', 'P003', 'P003'),
('C004', 'P004', 'P004'),
('C005', 'P005', 'P005'),
('C006', 'P006', 'P006'),
('C007', 'P007', 'P007'),
('C008', 'P008', 'P008'),
('C009', 'P009', 'P009'),
('C010', 'P010', 'P010'),
('C011', 'P022', 'P022'),
('C017', 'P023', 'P023'),
('C017', 'P003', 'P003')

-- Insert sample data for notifications
INSERT INTO notifications (notification_id, customer_id, message, due_date) VALUES
('N001', 'C001', 'Payment of ₹500 is due on 2025-03-31', '2025-03-31'),
('N002', 'C002', 'Payment of ₹1000 is due on 2025-03-30', '2025-03-30'),
('N003', 'C003', 'Payment of ₹750 is due on 2025-03-29', '2025-03-29'),
('N004', 'C004', 'Payment of ₹1200 is due on 2025-03-28', '2025-03-28'),
('N005', 'C005', 'Payment of ₹300 is due on 2025-03-27', '2025-03-27'),
('N006', 'C006', 'Payment of ₹450 is due on 2025-03-26', '2025-03-26'),
('N007', 'C007', 'Payment of ₹600 is due on 2025-03-25', '2025-03-25'),
('N008', 'C008', 'Payment of ₹850 is due on 2025-03-24', '2025-03-24'),
('N009', 'C009', 'Payment of ₹700 is due on 2025-03-23', '2025-03-23'),
('N010', 'C010', 'Payment of ₹900 is due on 2025-03-22', '2025-03-22'),
('N022', 'C011', 'Payment of ₹400 is due on 2025-04-20', '2025-04-20'),
('N023', 'C017', 'Payment of ₹500 is due on 2025-04-20', '2025-04-20')