from django.db.models import Func


class LevenshteinLessEqual(Func):
    """Django implementation of the Levenshtein distance function with a
    maximum distance (lenvenshtein_less_equal), brought by the fuzzystrmatch
    extension.

    See
    https://www.postgresql.org/docs/current/fuzzystrmatch.html#FUZZYSTRMATCH-LEVENSHTEIN.
    """

    template = "%(function)s(%(source)s, '%(target)s', %(ins_cost)d, %(del_cost)d, %(sub_cost)d, %(max_d)d)"
    function = "levenshtein_less_equal"

    def __init__(
        self,
        source: str,
        target: str,
        max_d: int,
        ins_cost=1,
        del_cost=1,
        sub_cost=1,
        **extras,
    ):
        super().__init__(
            source=source,
            target=target,
            ins_cost=ins_cost,
            del_cost=del_cost,
            sub_cost=sub_cost,
            max_d=max_d,
            **extras,
        )
