from collections import Counter

from django.core.management.base import BaseCommand
from django.db import models as dj_models, transaction

from open_prices.prices.models import Price


COUNTRY_DEFAULT_CURRENCY = {
    # Common mappings; extend as needed
    "FR": "EUR",
    "DE": "EUR",
    "ES": "EUR",
    "IT": "EUR",
    "NL": "EUR",
    "BE": "EUR",
    "PT": "EUR",
    "IE": "EUR",
    "AT": "EUR",
    "FI": "EUR",
    "US": "USD",
    "GB": "GBP",
    "CH": "CHF",
    "CA": "CAD",
    "AU": "AUD",
    "IN": "INR",
    "JP": "JPY",
    "CN": "CNY",
    "BR": "BRL",
    "MX": "MXN",
}


class Command(BaseCommand):
    help = (
        "Report and optionally fix prices with missing currency. "
        "By default it only reports. Use --write to apply defaults when possible."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--write",
            action="store_true",
            help="Apply default currency (from proof or location country).",
        )

    def handle(self, *args, **options):
        qs = Price.objects.filter(
            dj_models.Q(currency__isnull=True) | dj_models.Q(currency="")
        )
        count = qs.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS("No prices with missing currency."))
            return

        # Report by country code when available
        qs = qs.select_related("proof", "location")
        country_codes = [
            (p.location.osm_address_country_code if p.location else None) for p in qs
        ]
        by_country = Counter([c for c in country_codes if c])
        self.stdout.write(f"Prices with missing currency: {count}")
        if by_country:
            self.stdout.write("By country code:")
            for code, c in sorted(by_country.items()):
                self.stdout.write(f"  {code}: {c}")

        if not options.get("write"):
            self.stdout.write("Run with --write to attempt fixes.")
            return

        fixed = 0
        with transaction.atomic():
            for price in qs:
                new_currency = None
                # Prefer proof currency if present
                if price.proof and price.proof.currency:
                    new_currency = price.proof.currency
                # Else map from location country code
                elif price.location and price.location.osm_address_country_code:
                    new_currency = COUNTRY_DEFAULT_CURRENCY.get(
                        price.location.osm_address_country_code.upper()
                    )
                if new_currency:
                    price.currency = new_currency
                    price._change_reason = (
                        "fix_missing_price_currency management command (auto)"
                    )
                    # Save only this field to avoid triggering unrelated validations
                    price.save(update_fields=["currency"])
                    fixed += 1

        self.stdout.write(self.style.SUCCESS(f"Applied currency to {fixed} prices."))
