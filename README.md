# Local Vendor System

A web-based system for managing local vendors, customers, and products.

## Prerequisites

- Python 3.7 or higher
- MySQL Server 8.0 or higher
- pip (Python package installer)

## Setup Instructions

1. Clone the repository:
```bash
git clone <repository-url>
cd local_vendor_system
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Configure MySQL:
   - Create a new MySQL database
   - Update the database configuration in `app.py` with your MySQL credentials:
     ```python
     app.config['MYSQL_HOST'] = 'localhost'
     app.config['MYSQL_USER'] = 'your_username'
     app.config['MYSQL_PASSWORD'] = 'your_password'
     app.config['MYSQL_DB'] = 'your_database_name'
     ```

5. Initialize the database:
```bash
python init_db.py
```

## Running the Application

1. Start the Flask application:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

## Features

- Vendor Management
  - Add/Edit/Delete vendors
  - View vendor details
  - Manage vendor products

- Customer Management
  - Add/Edit/Delete customers
  - Track customer purchases
  - Manage customer payments

- Product Management
  - Add/Edit/Delete products
  - Track product inventory
  - View product sales

## Project Structure

```
local_vendor_system/
├── app.py              # Main Flask application
├── init_db.py          # Database initialization script
├── database.sql        # SQL schema and initial data
├── requirements.txt    # Python dependencies
├── static/            # Static files (CSS, JS, images)
└── templates/         # HTML templates
    ├── base.html
    ├── index.html
    ├── vendor_home.html
    └── customer_home.html
```

## Troubleshooting

1. Database Connection Issues:
   - Verify MySQL server is running
   - Check database credentials in `app.py`
   - Ensure database exists and is accessible

2. Application Errors:
   - Check Flask debug output for error messages
   - Verify all required packages are installed
   - Ensure virtual environment is activated

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 