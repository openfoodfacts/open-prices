def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False


def add_validation_error(dict, key, value):
    if key not in dict:
        dict[key] = value
    else:
        if type(dict[key]) is list:
            dict[key] += [value]
        if type(dict[key]) is str:
            dict[key] = [dict[key], value]
    return dict
