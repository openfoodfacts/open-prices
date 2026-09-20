import gzip
import json
import os
from pathlib import Path

import tqdm
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

from open_prices.api.locations.serializers import LocationSerializer
from open_prices.api.prices.serializers import PriceSerializer
from open_prices.api.proofs.serializers import ProofSerializer
from open_prices.locations.models import Location
from open_prices.prices.models import Price
from open_prices.proofs.models import Proof


def export_model_to_jsonl_gz(table_name, model_class, schema_class, output_dir):
    output_path = os.path.join(output_dir, f"{table_name}.jsonl.gz")
    with gzip.open(output_path, "wt") as f:
        for item in tqdm.tqdm(model_class.objects.all(), desc=table_name):
            f.write(json.dumps(schema_class(item).data, cls=DjangoJSONEncoder))
            f.write("\n")


def export_public_data():
    """
    Export the public data (prices, proofs, locations) as JSONL files
    to the data directory
    """
    output_dir = Path(os.path.join(settings.BASE_DIR, "data"))
    output_dir.mkdir(parents=True, exist_ok=True)

    for table_name, model_class, schema_class in (
        ("prices", Price, PriceSerializer),
        ("proofs", Proof, ProofSerializer),
        ("locations", Location, LocationSerializer),
    ):
        export_model_to_jsonl_gz(table_name, model_class, schema_class, output_dir)
