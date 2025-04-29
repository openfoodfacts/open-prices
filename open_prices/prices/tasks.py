from open_prices.challenges.models import Challenge
from open_prices.prices.models import Price


def update_tags(price: Price):
    changes = False
    # check if the price belongs to an ongoing challenge
    challenge_qs = Challenge.objects.is_ongoing()
    if challenge_qs.exists():
        for challenge in challenge_qs:
            if price.in_challenge(challenge):
                # update the price
                success = price.set_tag(challenge.tag, save=False)
                if success:
                    changes = True
                # update the price's proof
                if price.proof:
                    success = price.proof.set_tag(challenge.tag, save=True)
    if changes:
        price.save(update_fields=["tags"])
