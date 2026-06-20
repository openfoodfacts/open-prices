from django.db import IntegrityError
from django.test import TestCase

from open_prices.badges import constants as badge_constants
from open_prices.badges.factories import BadgeDefinitionFactory
from open_prices.users.factories import UserFactory


class BadgeDefinitionModelSaveTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_badge_definition_name_unique(self):
        BadgeDefinitionFactory(name="Test Badge")

        self.assertRaises(IntegrityError, BadgeDefinitionFactory, name="Test Badge")


class BadgeDefinitionPropertyTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def test_user_has_achieved_property(self):
        badge_definition = BadgeDefinitionFactory(
            metric=badge_constants.METRIC_PRICE_COUNT, threshold=5
        )

        self.assertEqual(self.user.price_count, 0)
        self.assertFalse(badge_definition.user_has_achieved(self.user))

        # Update the user's price_count to meet the threshold
        self.user.price_count = 5
        self.user.save()
        self.assertTrue(badge_definition.user_has_achieved(self.user))

        # Update again
        self.user.price_count = 10
        self.user.save()
        self.assertTrue(badge_definition.user_has_achieved(self.user))
