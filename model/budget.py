from typing import Optional
from datetime import datetime

class budget:
    def __init__(self, id: Optional[int], amount: float, category: str, start_date: str, end_date: str, user_id: int):
        self.id = id
        self.amount = amount
        self.category = category
        self.start_date = start_date
        self.end_date = end_date
        self.user_id = user_id
        self.created_at = datetime.now().isoformat()