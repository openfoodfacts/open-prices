from django.db.models import Field, Lookup


@Field.register_lookup
class Any(Lookup):
    """A custom lookup to check if a value is present in an array field."""

    lookup_name = "any"

    def as_sql(self, compiler, connection) -> tuple[str, list]:
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        # In PostgreSQL, to search in array fields, we can use the ANY
        # operator. The left-hand side (lhs) is the array field, and the
        # right-hand side (rhs) is the value we want to check against the
        # array. That's why we invert the order of lhs and rhs, as the SQL
        # syntax is: value = ANY (array_field)
        return "%s = ANY (%s)" % (rhs, lhs), params
