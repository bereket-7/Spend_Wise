class expense:
    def __init__(
        self,
        id: int,
        amount: float,
        category: str,
        date: str,
        user_id: int = None,
        description: str = None,
    ):
        self.id = id
        self.amount = amount
        self.category = category
        self.date = date
        self.user_id = user_id
        self.description = description
