from open_prices.common import utils


def validate_challenge_date_rules(instance):
    errors = dict()
    if instance.start_date and instance.end_date:
        if str(instance.start_date) > str(instance.end_date):
            utils.add_validation_error(
                errors,
                "start_date",
                "Should be before end_date",
            )
    return errors


def validate_challenge_published_rules(instance):
    errors = dict()
    if instance.is_published:
        if not instance.title:
            utils.add_validation_error(
                errors,
                "title",
                "Should be set if published is True",
            )
        if not instance.start_date:
            utils.add_validation_error(
                errors,
                "start_date",
                "Should be set if published is True",
            )
        if not instance.end_date:
            utils.add_validation_error(
                errors,
                "end_date",
                "Should be set if published is True",
            )
    return errors
