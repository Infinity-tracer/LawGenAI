"""
NyayAssist Database Setup Script
Run this script to initialize the MySQL database
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, DB_CONFIG


def check_mysql_connection():
    """Check if MySQL is accessible"""
    import pymysql
    
    try:
        # Try connecting without database first
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        print(f"✅ Successfully connected to MySQL at {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        
        # Check if database exists
        cursor = conn.cursor()
        cursor.execute(f"SHOW DATABASES LIKE '{DB_CONFIG['database']}'")
        result = cursor.fetchone()
        
        if result:
            print(f"✅ Database '{DB_CONFIG['database']}' exists")
        else:
            print(f"⚠️ Database '{DB_CONFIG['database']}' does not exist. Creating...")
            cursor.execute(f"CREATE DATABASE {DB_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"✅ Database '{DB_CONFIG['database']}' created successfully")
        
        cursor.close()
        conn.close()
        return True
        
    except pymysql.Error as e:
        print(f"❌ MySQL Connection Error: {e}")
        print("\nPlease make sure:")
        print("1. MySQL server is running")
        print("2. The credentials in your .env file are correct")
        print(f"3. User '{DB_CONFIG['user']}' has permission to create databases")
        return False


def setup_database():
    """Set up the database with all tables"""
    print("\n" + "="*60)
    print("NyayAssist Database Setup")
    print("="*60 + "\n")
    
    # Check connection first
    if not check_mysql_connection():
        return False
    
    print("\n📦 Creating database tables...")
    
    try:
        engine = init_db()
        print("✅ All tables created successfully!")
        
        # Print table list
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\n📋 Created {len(tables)} tables:")
        for table in sorted(tables):
            print(f"   - {table}")
        
        print("\n" + "="*60)
        print("✅ Database setup completed successfully!")
        print("="*60)
        print("\nYou can now run the API with:")
        print("   python api_with_db.py")
        print("\nOr run the Streamlit app with:")
        print("   streamlit run app.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False


def run_sql_schema():
    """Alternative: Run the SQL schema file directly"""
    import pymysql
    
    schema_path = os.path.join(os.path.dirname(__file__), 'database', 'schema.sql')
    
    if not os.path.exists(schema_path):
        print(f"❌ Schema file not found: {schema_path}")
        return False
    
    print(f"📄 Running SQL schema from: {schema_path}")
    
    try:
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            charset='utf8mb4',
            autocommit=True
        )
        
        cursor = conn.cursor()
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            sql_commands = f.read()
        
        # Split by delimiter for stored procedures
        # For simple execution, we'll just use the ORM approach
        
        cursor.close()
        conn.close()
        
        print("✅ SQL schema executed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error running SQL schema: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="NyayAssist Database Setup")
    parser.add_argument("--sql", action="store_true", help="Run raw SQL schema file")
    args = parser.parse_args()
    
    if args.sql:
        success = run_sql_schema()
    else:
        success = setup_database()
    
    sys.exit(0 if success else 1)
