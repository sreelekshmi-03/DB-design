
from rest_framework.pagination import PageNumberPagination, CursorPagination
class StandardResultsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
class JobFeedCursorPagination(CursorPagination):
    page_size = 10
    ordering = "-created_at"   # must match a real, indexed field
    cursor_query_param = "cursor"