from django.conf import settings
from rest_framework.exceptions import ParseError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    """
    docs: https://www.django-rest-framework.org/api-guide/pagination/#custom-pagination-styles  # noqa
    why do we override the pagination keys? we used to have fastapi-pagination before  # noqa
    - overridden keys: results -> items; count -> total
    - added keys: page, pages, size
    - removed keys: next, previous
    """

    ### page size config
    page_size = 10
    page_size_query_param = "size"  # default is None
    max_page_size = 100
    ### page number config
    # page_query_param = "page"  # default
    last_page_strings = ()  # disable "last" page string
    max_page_number = 500  # custom rule, see get_page_number()

    def get_page_number(self, request, paginator):
        """
        Override the default get_page_number

        Custom rule:
        - if the page number is greater than max_page_number, raise ParseError
        """
        page_number = super().get_page_number(request, paginator)
        try:
            page_number_int = int(page_number)
        except (TypeError, ValueError):
            raise ParseError("Invalid page.") from None
        if page_number_int < 1:
            raise ParseError("Invalid page.")
        if page_number_int > self.max_page_number:
            raise ParseError(
                f"Maximum page reached. See {settings.OPENPRICES_DOCS_GUIDES_DATA_URL} for alternate ways to access the data."
            )
        return page_number

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
                "items": schema,
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
