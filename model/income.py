from typing import Optional
from datetime import datetime

class income:
    def __init__(self, id: Optional[int], amount: float, source: str, date: str, user_id: int):
        self.id = id
        self.amount = amount
        self.source = source
        self.date = date
        self.user_id = user_id
        self.created_at = datetime.now().isoformat()