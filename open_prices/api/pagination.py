from rest_framework import pagination
from rest_framework.response import Response


class CustomPagination(pagination.PageNumberPagination):
    """
    https://www.django-rest-framework.org/api-guide/pagination/#custom-pagination-styles
    - results -> items
    - count -> total
    - next -> ?
    - previous -> ?
    """

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
