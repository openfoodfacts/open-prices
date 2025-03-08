from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    """
    docs: https://www.django-rest-framework.org/api-guide/pagination/#custom-pagination-styles  # noqa
    why do we override the pagination keys? we used to have fastapi-pagination before  # noqa
    - overriden keys: results -> items; count -> total
    - added keys: page, pages, size
    - removed keys: next, previous
    """

    page_size_query_param = "size"

    def get_paginated_response(self, data):
        return Response(
            {
                "items": data,
                "page": self.page.number,
                "pages": self.page.paginator.num_pages,
                "size": self.page.paginator.per_page,
                "total": self.page.paginator.count,
            }
        )

    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "required": ["items", "page", "pages", "size", "total"],
            "properties": {
                "items": {
                    "type": "array",
                    "items": schema,
                },
                "page": {
                    "type": "integer",
                    "description": "Current page number",
                    "example": 1,
                },
                "pages": {
                    "type": "integer",
                    "description": "Total number of pages",
                    "example": 16,
                },
                "size": {
                    "type": "integer",
                    "description": "Number of items per page",
                    "example": 100,
                },
                "total": {
                    "type": "integer",
                    "description": "Total number of items",
                    "example": 1531,
                },
            },
        }
