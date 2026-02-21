import logging
from typing import List, Optional, Dict, Any
from database.database_connection import get_connection, release_connection
from model.notification import notification

logger = logging.getLogger(__name__)

def create_notification(notification_data: Dict[str, Any]) -> bool:
    """Create a new notification"""
    connection = get_connection()
    if connection is None:
        return False
    
    try:
        cursor = connection.cursor()
        query = """
        INSERT INTO notification (notification_type, message, user_id, sent, read)
        VALUES (%s, %s, %s, %s, %s)
        """
        values = (
            notification_data['notification_type'],
            notification_data['message'],
            notification_data['user_id'],
            notification_data.get('sent', False),
            notification_data.get('read', False)
        )
        cursor.execute(query, values)
        connection.commit()
        logger.info(f"Notification created for user {notification_data['user_id']}")
        return True
    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        release_connection(connection)

def get_notification_by_id(notification_id: int) -> Optional[notification]:
    """Get notification by ID"""
    connection = get_connection()
    if connection is None:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM notification WHERE id = %s"
        cursor.execute(query, (notification_id,))
        result = cursor.fetchone()
        
        if result:
            return notification(
                id=result['id'],
                notification_type=result['notification_type'],
                message=result['message'],
                user_id=result['user_id'],
                sent=result['sent'],
                read=result['read']
            )
        return None
    except Exception as e:
        logger.error(f"Error getting notification: {e}")
        return None
    finally:
        cursor.close()
        release_connection(connection)

def get_notifications_by_user(user_id: int, unread_only: bool = False, limit: int = 50, offset: int = 0) -> List[notification]:
    """Get notifications for a user"""
    connection = get_connection()
    if connection is None:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        if unread_only:
            query = "SELECT * FROM notification WHERE user_id = %s AND read = %s ORDER BY created_at DESC LIMIT %s OFFSET %s"
            cursor.execute(query, (user_id, False, limit, offset))
        else:
            query = "SELECT * FROM notification WHERE user_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s"
            cursor.execute(query, (user_id, limit, offset))
        
        results = cursor.fetchall()
        
        notifications = []
        for result in results:
            notifications.append(notification(
                id=result['id'],
                notification_type=result['notification_type'],
                message=result['message'],
                user_id=result['user_id'],
                sent=result['sent'],
                read=result['read']
            ))
        return notifications
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return []
    finally:
        cursor.close()
        release_connection(connection)

def mark_notification_as_read(notification_id: int, user_id: int) -> bool:
    """Mark notification as read"""
    connection = get_connection()
    if connection is None:
        return False
    
    try:
        cursor = connection.cursor()
        query = "UPDATE notification SET read = %s WHERE id = %s AND user_id = %s"
        cursor.execute(query, (True, notification_id, user_id))
        connection.commit()
        logger.info(f"Notification {notification_id} marked as read")
        return True
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        release_connection(connection)

def mark_all_notifications_as_read(user_id: int) -> bool:
    """Mark all notifications as read for a user"""
    connection = get_connection()
    if connection is None:
        return False
    
    try:
        cursor = connection.cursor()
        query = "UPDATE notification SET read = %s WHERE user_id = %s AND read = %s"
        cursor.execute(query, (True, user_id, False))
        connection.commit()
        logger.info(f"All notifications marked as read for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        release_connection(connection)

def delete_notification(notification_id: int, user_id: int) -> bool:
    """Delete notification"""
    connection = get_connection()
    if connection is None:
        return False
    
    try:
        cursor = connection.cursor()
        query = "DELETE FROM notification WHERE id = %s AND user_id = %s"
        cursor.execute(query, (notification_id, user_id))
        connection.commit()
        logger.info(f"Notification {notification_id} deleted")
        return True
    except Exception as e:
        logger.error(f"Error deleting notification: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        release_connection(connection)

def get_unread_count(user_id: int) -> int:
    """Get count of unread notifications for a user"""
    connection = get_connection()
    if connection is None:
        return 0
    
    try:
        cursor = connection.cursor()
        query = "SELECT COUNT(*) FROM notification WHERE user_id = %s AND read = %s"
        cursor.execute(query, (user_id, False))
        result = cursor.fetchone()
        return result[0] if result else 0
    except Exception as e:
        logger.error(f"Error getting unread count: {e}")
        return 0
    finally:
        cursor.close()
        release_connection(connection)

def create_budget_alert(budget_id: int, user_id: int, percentage_used: float, category: str) -> bool:
    """Create budget alert notification"""
    if percentage_used >= 100:
        message = f"Budget Alert: You have exceeded your {category} budget by {percentage_used - 100:.1f}%!"
        notification_type = "budget_exceeded"
    elif percentage_used >= 80:
        message = f"Budget Warning: You have used {percentage_used:.1f}% of your {category} budget."
        notification_type = "budget_warning"
    else:
        return False  # No notification needed
    
    notification_data = {
        'notification_type': notification_type,
        'message': message,
        'user_id': user_id,
        'sent': True
    }
    
    return create_notification(notification_data)
