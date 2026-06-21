from django.db import IntegrityError
from django.test import TestCase

from open_prices.badges import constants as badge_constants
from open_prices.badges.factories import BadgeFactory
from open_prices.badges.models import UserBadge
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
        cls.badge = BadgeFactory(metric=badge_constants.METRIC_PRICE_COUNT, threshold=5)

    def test_user_has_achieved_property(self):
        # Initially, the user has 0 prices
        self.assertEqual(self.user.price_count, 0)
        self.assertFalse(self.badge.user_has_achieved(self.user))

        # Update the user's price_count to meet the threshold
        self.user.price_count = 5
        self.user.save()
        self.assertTrue(self.badge.user_has_achieved(self.user))

        # Update again
        self.user.price_count = 10
        self.user.save()
        self.assertTrue(self.badge.user_has_achieved(self.user))

    def test_update_user_badges_and_count(self):
        # Initially, the user has 0 prices and no badges
        self.assertEqual(self.user.price_count, 0)
        self.assertEqual(UserBadge.objects.count(), 0)
        self.assertEqual(self.badge.user_badges.count(), 0)
        self.assertEqual(self.badge.user_count, 0)

        # Update the user's price_count to meet the threshold
        self.user.price_count = 5
        self.user.save()

        # Update user badges and count
        self.badge.update_user_badges()
        self.badge.update_user_count()

        # Stats should be updated correctly
        self.assertEqual(UserBadge.objects.count(), 1)
        self.assertEqual(self.badge.user_badges.count(), 1)
        self.assertEqual(self.badge.user_count, 1)
        user_badge_achieved_at = UserBadge.objects.get(
            user=self.user, badge=self.badge
        ).achieved_at
        self.assertIsNotNone(user_badge_achieved_at)

        # Create another badge + another user who meets both thresholds
        badge_2 = BadgeFactory(metric=badge_constants.METRIC_PRICE_COUNT, threshold=10)
        UserFactory(price_count=15)

        # Update user badges and count for both badges
        for badge in [self.badge, badge_2]:
            badge.update_user_badges()
            badge.update_user_count()

        # Stats should be updated correctly for both badges
        self.assertEqual(UserBadge.objects.count(), 2 + 1)
        self.assertEqual(self.badge.user_badges.count(), 2)
        self.assertEqual(self.badge.user_count, 2)
        self.assertEqual(badge_2.user_badges.count(), 1)
        self.assertEqual(badge_2.user_count, 1)
        # user_badge_achieved_at is unchanged
        self.assertEqual(
            UserBadge.objects.get(user=self.user, badge=self.badge).achieved_at,
            user_badge_achieved_at,
        )
