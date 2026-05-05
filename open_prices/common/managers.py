from django.db import connections
from django.db.models import Manager, QuerySet


class ApproximateCountQuerySet(QuerySet):
    """Use PostgreSQL's pg_class.reltuples for fast approximate counting.

    For large tables, COUNT(*) requires a full table scan which is slow.
    This queryset uses PostgreSQL's internal table statistics (reltuples)
    for unfiltered counts, providing significant performance improvement.

    Falls back to exact COUNT(*) when filters are applied to maintain accuracy.
    Relies on PostgreSQL's autovacuum to keep statistics up-to-date.
    """

    def count(self):
        if self.query.where:
            return super().count()

        cursor = connections[self.db].cursor()
        cursor.execute(
            "SELECT reltuples::bigint FROM pg_class "
            "WHERE relname = %s AND relkind = 'r';",
            [self.model._meta.db_table],
        )
        row = cursor.fetchone()

        if row and row[0] > 0:
            return int(row[0])

        return super().count()


ApproximateCountManager = Manager.from_queryset(ApproximateCountQuerySet)
