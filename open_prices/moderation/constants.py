from functools import reduce
from operator import or_

from django.db.models import Q

FLAG_ALLOWED_CONTENT_TYPES_LIST = [
    # ("app_label", "model"),
    ("prices", "price"),
    ("proofs", "proof"),
]

FLAG_ALLOWED_CONTENT_TYPES_QUERY_LIST = reduce(
    or_,
    (
        Q(app_label=app_label, model=model)
        for app_label, model in FLAG_ALLOWED_CONTENT_TYPES_LIST
    ),
)
