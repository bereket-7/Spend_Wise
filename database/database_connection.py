import os
import logging
from mysql.connector import pooling
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration from environment variables
db_config = {
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '8915code'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'spend_wise'),
    'auth_plugin': 'mysql_native_password'
}

# Connection pool configuration
connection_pool = None

def initialize_connection_pool(pool_name: str = "spend_wise_pool", pool_size: int = 5):
    """Initialize database connection pool"""
    global connection_pool
    try:
        connection_pool = pooling.MySQLConnectionPool(
            pool_name=pool_name,
            pool_size=pool_size,
            **db_config
        )
        logger.info("Database connection pool initialized successfully!")
        return connection_pool
    except Exception as e:
        logger.error(f"Error initializing connection pool: {e}")
        return None

def get_connection() -> Optional[object]:
    """Get connection from pool"""
    global connection_pool
    if connection_pool is None:
        initialize_connection_pool()
    
    try:
        connection = connection_pool.get_connection()
        logger.debug("Database connection established from pool!")
        return connection
    except Exception as e:
        logger.error(f"Error getting connection from pool: {e}")
        return None

def release_connection(connection):
    """Release connection back to pool"""
    if connection and connection.is_connected():
        connection.close()
        logger.debug("Database connection released back to pool")

def close_all_connections():
    """Close all connections in the pool"""
    global connection_pool
    if connection_pool:
        connection_pool._remove_connections()
        logger.info("All database connections closed.")