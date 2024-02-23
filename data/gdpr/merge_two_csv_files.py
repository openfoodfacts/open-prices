import csv
import os


def read_csv(filepath):
    data = list()

    with open(filepath, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(row)

    return data


def merge_data_of_two_lists(list_1, list_2, pivot="ticket"):
    data_merged = list()

    for row_1 in list_1:
        pivot_1 = row_1[pivot]
        row_2 = next(row for row in list_2 if row[pivot] == pivot_1)
        data_merged.append({**row_1, **row_2})

    return data_merged


def write_csv(data, filepath):
    keys = data[0].keys()

    with open(filepath, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, keys)
        writer.writeheader()
        writer.writerows(data)


if __name__ == "__main__":
    """
    How-to run:
    > FILEPATH_1= FILEPATH_2= PIVOT_FIELD_NAME= poetry run python data/gdpr/merge_two_csv_files.py  # noqa
    """
    filepath_1 = os.environ.get("FILEPATH_1")
    filepath_2 = os.environ.get("FILEPATH_2")
    pivot_field_name = os.environ.get("PIVOT_FIELD_NAME")
    output_filepath = filepath_1.split(".csv")[0] + "_merged.csv"

    print(f"Step 1: reading {filepath_1}")
    data_1 = read_csv(filepath_1)
    print(f"{len(data_1)} lines")

    print(f"Step 2: reading {filepath_2}")
    data_2 = read_csv(filepath_2)
    print(f"{len(data_2)} lines")

    print("Step 3: merging the two lists")
    data_merged = merge_data_of_two_lists(data_1, data_2, pivot=pivot_field_name)
    print(f"{len(data_merged)} lines")

    print("Step 4: write CSV")
    write_csv(data_merged, output_filepath)
