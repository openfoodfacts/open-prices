# Generated manually on 2025-09-22 15:22

from django.contrib.postgres.operations import CreateExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0006_alter_product_source"),
    ]

    operations = [CreateExtension("fuzzystrmatch")]
