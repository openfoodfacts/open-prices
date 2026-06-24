from django.db import IntegrityError
from django.test import TestCase

from open_prices.badges import constants as badge_constants
from open_prices.badges.factories import BadgeFactory
from open_prices.users.factories import UserFactory


class BadgeModelSaveTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_badge_name_unique(self):
        BadgeFactory(name="Test Badge")

        self.assertRaises(IntegrityError, BadgeFactory, name="Test Badge")


class BadgePropertyTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def test_user_has_achieved_property(self):
        badge = BadgeFactory(metric=badge_constants.METRIC_PRICE_COUNT, threshold=5)

        self.assertEqual(self.user.price_count, 0)
        self.assertFalse(badge.user_has_achieved(self.user))

        # Update the user's price_count to meet the threshold
        self.user.price_count = 5
        self.user.save()
        self.assertTrue(badge.user_has_achieved(self.user))

        # Update again
        self.user.price_count = 10
        self.user.save()
        self.assertTrue(badge.user_has_achieved(self.user))
