from django.db import IntegrityError
from django.test import TestCase

from open_prices.badges import constants as badge_constants
from open_prices.badges.factories import BadgeFactory
from open_prices.badges.models import Badge, UserBadge
from open_prices.users.factories import UserFactory


class BadgeModelSaveTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_badge_name_unique(self):
        BadgeFactory(name="Test Badge")

        self.assertRaises(IntegrityError, BadgeFactory, name="Test Badge")


class BadgeQuerySetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.badge_5 = BadgeFactory(
            metric=badge_constants.METRIC_PRICE_COUNT, threshold=5
        )
        cls.badge_50 = BadgeFactory(
            metric=badge_constants.METRIC_PRICE_COUNT, threshold=50
        )

    def test_has_users(self):
        UserFactory(price_count=0)
        UserFactory(price_count=10)

        Badge.update_task()

        self.assertEqual(Badge.objects.count(), 2)
        self.assertEqual(Badge.objects.has_users().count(), 1)


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

    def test_when_user_meets_threshold_update_user_badges_and_count(self):
        # Initially, the user has 0 prices and no badges
        self.assertEqual(self.user.price_count, 0)
        self.assertEqual(UserBadge.objects.count(), 0)
        self.assertEqual(self.badge.user_badges.count(), 0)
        self.assertEqual(self.badge.user_count, 0)

        # Update the user's price_count to meet the threshold
        self.user.price_count = 5
        self.user.save()

        # Update user badges and count
        Badge.update_task()
        self.badge.refresh_from_db()

        # Stats should be updated correctly
        self.assertEqual(UserBadge.objects.count(), 1)
        self.assertEqual(self.badge.user_badges.count(), 1)
        self.assertEqual(self.badge.user_count, 1)
        user_badge_achieved_at = UserBadge.objects.get(
            user=self.user, badge=self.badge
        ).achieved_at
        self.assertIsNotNone(user_badge_achieved_at)

    def test_when_user_already_has_badge_do_not_update_achieved_at(self):
        # Make the user meet the threshold and update badges
        self.user.price_count = 5
        self.user.save()

        # Update user badges and count
        Badge.update_task()
        self.badge.refresh_from_db()
        user_badge_achieved_at = UserBadge.objects.get(
            user=self.user, badge=self.badge
        ).achieved_at

        # Update user badges and count again
        Badge.update_task()
        self.badge.refresh_from_db()

        # user_badge_achieved_at is unchanged
        self.assertEqual(
            UserBadge.objects.get(user=self.user, badge=self.badge).achieved_at,
            user_badge_achieved_at,
        )

    def test_when_user_meets_multiple_thresholds_update_user_badges_and_counts(self):
        # Create another badge with a different threshold
        badge_2 = BadgeFactory(metric=badge_constants.METRIC_PRICE_COUNT, threshold=10)

        # Make the user meet the threshold for both badges
        self.user.price_count = 15
        self.user.save()

        # Update user badges and count
        Badge.update_task()
        self.badge.refresh_from_db()
        badge_2.refresh_from_db()

        # Stats should be updated correctly for both badges
        self.assertEqual(UserBadge.objects.count(), 2)
        self.assertEqual(self.badge.user_badges.count(), 1)
        self.assertEqual(self.badge.user_count, 1)
        self.assertEqual(badge_2.user_badges.count(), 1)
        self.assertEqual(badge_2.user_count, 1)

    def test_when_user_does_not_meet_threshold_anymore_badge_is_not_removed(self):
        # Make the user meet the threshold
        self.user.price_count = 5
        self.user.save()

        # Update user badges and count
        Badge.update_task()
        self.badge.refresh_from_db()
        user_badge_achieved_at = UserBadge.objects.get(
            user=self.user, badge=self.badge
        ).achieved_at

        # Now, reduce the user's price_count below the threshold
        self.user.price_count = 3
        self.user.save()

        # Update user badges and count again
        Badge.update_task()
        self.badge.refresh_from_db()

        # The badge should still be present for the user
        self.assertEqual(
            UserBadge.objects.filter(user=self.user, badge=self.badge).count(), 1
        )
        self.assertEqual(
            UserBadge.objects.get(user=self.user, badge=self.badge).achieved_at,
            user_badge_achieved_at,
        )
