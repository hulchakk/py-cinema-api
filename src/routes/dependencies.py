from fastapi import Query


class PaginationParams:
    def __init__(
        self,
        page: int = Query(default=1, ge=1),
        per_page: int = Query(default=10, ge=1, le=100),
    ):
        self.page = page
        self.per_page = per_page
        self.offset = (page - 1) * per_page
        self.limit = per_page
