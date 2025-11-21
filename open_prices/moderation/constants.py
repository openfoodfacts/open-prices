FLAG_ALLOWED_CONTENT_TYPE_CHOICES = [
    # ("app_label", "model"),
    ("prices", "price"),
    ("proofs", "proof"),
]

FLAG_ALLOWED_CONTENT_TYPE_CHOICES_UPPER = [
    # ("MODEL", "Model"),
    (model.upper(), model.capitalize())
    for app_label, model in FLAG_ALLOWED_CONTENT_TYPE_CHOICES
]

FLAG_ALLOWED_CONTENT_TYPE_LIST = [
    model for app_label, model in FLAG_ALLOWED_CONTENT_TYPE_CHOICES
]
