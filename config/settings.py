"""
Configuration management for Spend Wise application
"""
import os
from typing import Any, Dict, Optional
from dataclasses import dataclass
from enum import Enum

class Environment(Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"

@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str
    port: int
    database: str
    user: str
    password: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600

@dataclass
class JWTConfig:
    """JWT configuration"""
    secret_key: str
    algorithm: str = "HS256"
    token_expiry_hours: int = 24
    refresh_token_days: int = 7

@dataclass
class ServerConfig:
    """Server configuration"""
    host: str = "localhost"
    port: int = 8000
    debug: bool = False
    workers: int = 1

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5

@dataclass
class AppConfig:
    """Main application configuration"""
    environment: Environment
    database: DatabaseConfig
    jwt: JWTConfig
    server: ServerConfig
    logging: LoggingConfig
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Create configuration from environment variables"""
        env = Environment(os.getenv('ENVIRONMENT', 'development'))
        
        return cls(
            environment=env,
            database=DatabaseConfig(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', '3306')),
                database=os.getenv('DB_NAME', 'spend_wise'),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', ''),
                pool_size=int(os.getenv('DB_POOL_SIZE', '10')),
                max_overflow=int(os.getenv('DB_MAX_OVERFLOW', '20'))
            ),
            jwt=JWTConfig(
                secret_key=os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production'),
                algorithm=os.getenv('JWT_ALGORITHM', 'HS256'),
                token_expiry_hours=int(os.getenv('TOKEN_EXPIRY_HOURS', '24')),
                refresh_token_days=int(os.getenv('REFRESH_TOKEN_DAYS', '7'))
            ),
            server=ServerConfig(
                host=os.getenv('SERVER_HOST', 'localhost'),
                port=int(os.getenv('SERVER_PORT', '8000')),
                debug=os.getenv('DEBUG', 'false').lower() == 'true',
                workers=int(os.getenv('WORKERS', '1'))
            ),
            logging=LoggingConfig(
                level=os.getenv('LOG_LEVEL', 'INFO'),
                file_path=os.getenv('LOG_FILE_PATH'),
                max_file_size=int(os.getenv('LOG_MAX_FILE_SIZE', str(10 * 1024 * 1024))),
                backup_count=int(os.getenv('LOG_BACKUP_COUNT', '5'))
            )
        )
    
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment == Environment.DEVELOPMENT
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment == Environment.PRODUCTION
    
    def is_testing(self) -> bool:
        """Check if running in testing mode"""
        return self.environment == Environment.TESTING

# Global configuration instance
config = AppConfig.from_env()
