"""
Base repository pattern for database operations
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, TypeVar, Generic
from contextlib import contextmanager
import logging

from database.database_connection import get_connection, release_connection

T = TypeVar('T')

logger = logging.getLogger(__name__)

class BaseRepository(ABC, Generic[T]):
    """Base repository with common database operations"""
    
    def __init__(self, model_class: type):
        self.model_class = model_class
        self.table_name = self._get_table_name()
    
    @abstractmethod
    def _get_table_name(self) -> str:
        """Get the table name for this repository"""
        pass
    
    @abstractmethod
    def _model_to_dict(self, model: T) -> Dict[str, Any]:
        """Convert model instance to dictionary"""
        pass
    
    @abstractmethod
    def _dict_to_model(self, data: Dict[str, Any]) -> T:
        """Convert dictionary to model instance"""
        pass
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        connection = get_connection()
        try:
            yield connection
        finally:
            release_connection(connection)
    
    def create(self, model: T) -> Optional[T]:
        """Create a new record"""
        try:
            with self._get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                data = self._model_to_dict(model)
                columns = list(data.keys())
                placeholders = ', '.join(['%s'] * len(columns))
                
                query = f"""
                INSERT INTO {self.table_name} ({', '.join(columns)})
                VALUES ({placeholders})
                """
                
                values = list(data.values())
                cursor.execute(query, values)
                connection.commit()
                
                # Get the inserted ID
                model.id = cursor.lastrowid
                return model
                
        except Exception as e:
            logger.error(f"Error creating {self.table_name}: {e}")
            return None
    
    def get_by_id(self, id: int) -> Optional[T]:
        """Get a record by ID"""
        try:
            with self._get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                query = f"SELECT * FROM {self.table_name} WHERE id = %s"
                cursor.execute(query, (id,))
                result = cursor.fetchone()
                
                if result:
                    return self._dict_to_model(result)
                return None
                
        except Exception as e:
            logger.error(f"Error getting {self.table_name} by ID {id}: {e}")
            return None
    
    def get_all(self, limit: int = None, offset: int = None) -> List[T]:
        """Get all records with optional pagination"""
        try:
            with self._get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                query = f"SELECT * FROM {self.table_name}"
                
                if limit:
                    query += f" LIMIT {limit}"
                if offset:
                    query += f" OFFSET {offset}"
                
                cursor.execute(query)
                results = cursor.fetchall()
                
                return [self._dict_to_model(result) for result in results]
                
        except Exception as e:
            logger.error(f"Error getting all {self.table_name}: {e}")
            return []
    
    def update(self, model: T) -> Optional[T]:
        """Update a record"""
        try:
            with self._get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                data = self._model_to_dict(model)
                columns = [key for key in data.keys() if key != 'id']
                set_clause = ', '.join([f"{col} = %s" for col in columns])
                
                query = f"""
                UPDATE {self.table_name}
                SET {set_clause}
                WHERE id = %s
                """
                
                values = [data[col] for col in columns] + [model.id]
                cursor.execute(query, values)
                connection.commit()
                
                return model
                
        except Exception as e:
            logger.error(f"Error updating {self.table_name}: {e}")
            return None
    
    def delete(self, id: int) -> bool:
        """Delete a record by ID"""
        try:
            with self._get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                query = f"DELETE FROM {self.table_name} WHERE id = %s"
                cursor.execute(query, (id,))
                connection.commit()
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error deleting {self.table_name} with ID {id}: {e}")
            return False
    
    def count(self) -> int:
        """Count total records"""
        try:
            with self._get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                query = f"SELECT COUNT(*) as count FROM {self.table_name}"
                cursor.execute(query)
                result = cursor.fetchone()
                
                return result['count'] if result else 0
                
        except Exception as e:
            logger.error(f"Error counting {self.table_name}: {e}")
            return 0
    
    def find_by_field(self, field: str, value: Any) -> List[T]:
        """Find records by a specific field"""
        try:
            with self._get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                query = f"SELECT * FROM {self.table_name} WHERE {field} = %s"
                cursor.execute(query, (value,))
                results = cursor.fetchall()
                
                return [self._dict_to_model(result) for result in results]
                
        except Exception as e:
            logger.error(f"Error finding {self.table_name} by {field}: {e}")
            return []
