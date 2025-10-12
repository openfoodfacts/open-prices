import gzip
import json
import os
from decimal import Decimal
from urllib.parse import urlparse

import tqdm
from django.core.serializers.json import DjangoJSONEncoder


def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False


def truncate_decimal(value, max_decimal_places=7):
    if value:
        if type(value) is str:
            if "." in value:
                integer_part, decimal_part = value.split(".")
                if len(decimal_part) > max_decimal_places:
                    decimal_part = decimal_part[:max_decimal_places]
                value = f"{integer_part}.{decimal_part}"
    return value


def match_decimal_with_float(price_decimal: Decimal, price_float: float) -> bool:
    return float(price_decimal) == price_float


def add_validation_error(dict, key, value):
    """
    Build a dictionary of validation errors
    {"field1": ["error1", "error2"], "field2": ["error1"]}
    """
    if key not in dict:
        dict[key] = value
    else:
        if type(dict[key]) is list:
            dict[key] += [value]
        if type(dict[key]) is str:
            dict[key] = [dict[key], value]
    return dict


def merge_validation_errors(dict1, *args):
    for dict2 in args:
        for key, value in dict2.items():
            dict1 = add_validation_error(dict1, key, value)
    return dict1


def export_model_to_jsonl_gz(table_name, model_class, schema_class, output_dir):
    output_path = os.path.join(output_dir, f"{table_name}.jsonl.gz")
    with gzip.open(output_path, "wt") as f:
        for item in tqdm.tqdm(model_class.objects.all(), desc=table_name):
            f.write(json.dumps(schema_class(item).data, cls=DjangoJSONEncoder))
            f.write("\n")


def url_add_missing_https(url):
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


def url_keep_only_domain(url):
    """
    - input: http://abc.hostname.com/somethings/anything/
    - urlparse: ParseResult(scheme='http', netloc='abc.hostname.com', path='/somethings/anything/', params='', query='', fragment='')  # noqa
    - output: http://abc.hostname.com
    """
    if not url.startswith(("http://", "https://")):
        url = url_add_missing_https(url)
    url_parsed = urlparse(url)
    return f"{url_parsed.scheme}://{url_parsed.netloc}"
