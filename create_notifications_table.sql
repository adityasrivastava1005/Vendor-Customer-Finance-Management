CREATE TABLE IF NOT EXISTS notifications (
    notification_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50),
    message TEXT,
    due_date DATE,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customer(Customer_id)
); 