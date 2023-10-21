import peewee
from playhouse.postgres_ext import BinaryJSONField, PostgresqlExtDatabase
from playhouse.shortcuts import model_to_dict

from app.config import settings

db = PostgresqlExtDatabase(
    settings.postgres_db_name,
    user=settings.postgres_user,
    password=settings.postgres_password,
    host=settings.postgres_host,
    port=settings.postgres_port,
    autoconnect=False,
)


class BaseModel(peewee.Model):
    class Meta:
        database = db
        legacy_table_names = False

    def to_dict(self, **kwargs):
        return model_to_dict(self, **kwargs)


class Task(BaseModel):
    """Table to store moderation or data quality tasks."""

    # Barcode represents the barcode of the product for which the insight was
    # generated. It is prefixed by `{ORG_ID}/` for the pro platform.
    barcode = peewee.CharField(max_length=100, null=False, index=True)

    # Type represents the task type - must match one of the types in
    # robotoff.types.TaskType.
    type = peewee.CharField(max_length=256, index=True)

    # Contains some additional data based on the type of the task from
    # above.
    data = BinaryJSONField(index=True, default=dict)

    # created_at is the timestamp of when this task was created in the DB.
    created_at = peewee.DateTimeField(null=True, index=True)

    # Stores the timestamp of when this task was completed, either by a
    # human or automatically.
    completed_at = peewee.DateTimeField(null=True)

    # boolean indicating if the task has been completed, either automatically
    # or by a human
    is_completed = peewee.BooleanField(null=True, index=True)

    # If the insight was annotated manually, this field stores the username of
    # the annotator (or first annotator, if multiple votes were cast).
    completed_by = peewee.TextField(index=True, null=True)

    # Specifies the timestamp on a task (that can be applied automatically)
    # after which the task should be applied.
    process_after = peewee.DateTimeField(null=True)

    # If the task is about an image, this field points to that image.
    image = peewee.ForeignKeyField(ImageModel, null=False, backref="tasks")

    # Automatic processing is set on tasks where no human intervention is
    # necessary.
    automatic_processing = peewee.BooleanField(default=False, index=True)

    # the server_type specifies which project we're using
    server_type = peewee.CharField(
        null=True,
        max_length=10,
        help_text="project associated with the insight, "
        "one of 'off', 'obf', 'opff', 'opf', 'off-pro'",
        index=True,
    )

    def get_product_id(self) -> ProductIdentifier:
        return ProductIdentifier(self.barcode, ServerType[self.server_type])
