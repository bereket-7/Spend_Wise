from typing import Optional
from datetime import datetime

class notification:
    def __init__(self, id: Optional[int], notification_type: str, message: str, user_id: int, sent: bool = False, read: bool = False):
        self.id = id
        self.notification_type = notification_type
        self.message = message
        self.user_id = user_id
        self.sent = sent
        self.read = read
        self.created_at = datetime.now().isoformat()
        self.sent_at = None if not sent else datetime.now().isoformat()