from django.db import connections
from django.db.models import Manager, QuerySet


class ApproximateCountQuerySet(QuerySet):
    def count(self):
        if self.query.where:
            return super().count()

        cursor = connections[self.db].cursor()
        cursor.execute(
            "SELECT reltuples::bigint FROM pg_class WHERE relname = %s;",
            [self.model._meta.db_table],
        )
        row = cursor.fetchone()

        if row and row[0] > 0:
            return int(row[0])

        return super().count()


ApproximateCountManager = Manager.from_queryset(ApproximateCountQuerySet)
