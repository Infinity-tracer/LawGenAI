"""
NyayAssist Database Configuration
MySQL Database connection and configuration settings
"""

import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", 3306)),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "nyayassist_db"),
    "charset": "utf8mb4",
    "collation": "utf8mb4_unicode_ci",
    "autocommit": True,
    "pool_size": 5,
    "pool_name": "nyayassist_pool"
}

# SQLAlchemy Database URL
def get_database_url():
    """Get SQLAlchemy database URL"""
    # URL-encode password to handle special characters like @, #, etc.
    encoded_password = quote_plus(DB_CONFIG['password'])
    return (
        f"mysql+pymysql://{DB_CONFIG['user']}:{encoded_password}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        f"?charset={DB_CONFIG['charset']}"
    )

# Async Database URL for async operations
def get_async_database_url():
    """Get async SQLAlchemy database URL"""
    # URL-encode password to handle special characters like @, #, etc.
    encoded_password = quote_plus(DB_CONFIG['password'])
    return (
        f"mysql+aiomysql://{DB_CONFIG['user']}:{encoded_password}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        f"?charset={DB_CONFIG['charset']}"
    )
