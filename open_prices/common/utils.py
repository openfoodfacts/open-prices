import gzip
import json

import tqdm


def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False


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


def export_model_to_jsonl_gz(table_name, model_class, schema_class, output_dir):
    output_path = output_dir / f"{table_name}.jsonl.gz"
    with gzip.open(output_path, "wt") as f:
        for item in tqdm.tqdm(model_class.objects.all(), desc=table_name):
            f.write(json.dumps(schema_class(item).data))
            f.write("\n")


def truncate_decimal(value, max_decimal_places=7):
    if value:
        if type(value) is str:
            if "." in value:
                integer_part, decimal_part = value.split(".")
                if len(decimal_part) > max_decimal_places:
                    decimal_part = decimal_part[:max_decimal_places]
                value = f"{integer_part}.{decimal_part}"
    return value
