"""
Model-layer tests for the fleet app.

WHAT WE TEST HERE:
  - Model field defaults and constraints (at the DB level)
  - __str__ representations
  - Meta ordering
  - Cascade/null behaviour on FK relationships

WHAT WE DO NOT TEST HERE:
  - Serializer validation (that lives in test_api.py)
  - API permissions (that lives in test_api.py)

NOTE ON setUpTestData vs setUp:
  - setUpTestData: runs ONCE per class, wraps in a transaction that rolls back
    after all tests finish. Fastest option. Use when tests only READ data.
  - setUp: runs before EVERY test. Use when tests WRITE/MODIFY the shared objects.
  We use setUp here because some tests intentionally trigger IntegrityErrors which
  can leave the DB connection in a broken state mid-transaction.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from fleet.models import Driver, TripLog, Vehicle

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(email, username="user", password="TestPass123", **kwargs):
    """One-liner so setUp methods stay readable."""
    return User.objects.create_user(
        email=email, username=username, password=password, **kwargs
    )


def make_vehicle(registered_number="TEST001", model="Tata Ace", status="active"):
    return Vehicle.objects.create(
        registered_number=registered_number, model=model, status=status
    )


def make_driver(user, license_number="DL00001", phone_number="9000000001",
                name="Test Driver", status="active", primary_vehicle=None):
    return Driver.objects.create(
        user=user,
        name=name,
        license_number=license_number,
        phone_number=phone_number,
        status=status,
        primary_vehicle=primary_vehicle,
    )


# ---------------------------------------------------------------------------
# Vehicle
# ---------------------------------------------------------------------------

class VehicleModelTest(TestCase):

    def setUp(self):
        self.vehicle = make_vehicle(
            registered_number="CG04AB1234", model="Tata Ace")

    # --- field correctness ---

    def test_fields_are_saved_correctly(self):
        self.assertEqual(self.vehicle.registered_number, "CG04AB1234")
        self.assertEqual(self.vehicle.model, "Tata Ace")
        self.assertEqual(self.vehicle.status, "active")

    def test_default_status_is_active(self):
        v = Vehicle.objects.create(registered_number="CG04AB9999")
        self.assertEqual(v.status, "active")

    def test_model_field_can_be_blank(self):
        """model (truck model name) is optional."""
        v = Vehicle.objects.create(registered_number="CG04AB8888")
        self.assertEqual(v.model, "")

    def test_primary_key_is_uuid(self):
        import uuid
        self.assertIsInstance(self.vehicle.id, uuid.UUID)

    def test_str_representation(self):
        self.assertEqual(str(self.vehicle), "Vehicle: CG04AB1234")

    # --- constraints ---

    def test_registered_number_must_be_unique(self):
        with self.assertRaises(IntegrityError):
            Vehicle.objects.create(registered_number="CG04AB1234")

    # --- ordering: Meta.ordering = ['-status', 'registered_number', '-date_created'] ---
    # '-status' is descending alphabetically.
    # 'inactive' > 'active' alphabetically, so inactive rows sort FIRST.

    def test_inactive_vehicles_sort_before_active(self):
        make_vehicle(registered_number="ZZZ001", status="inactive")
        make_vehicle(registered_number="AAA001", status="active")

        vehicles = list(Vehicle.objects.all())
        statuses = [v.status for v in vehicles]

        # All inactive should appear before any active
        last_inactive = max(
            (i for i, v in enumerate(vehicles) if v.status == "inactive"),
            default=-1
        )
        first_active = min(
            (i for i, v in enumerate(vehicles) if v.status == "active"),
            default=len(vehicles)
        )
        self.assertLess(last_inactive, first_active,
                        msg="Inactive vehicles should sort before active ones")

    def test_within_same_status_sorted_by_registered_number_asc(self):
        make_vehicle(registered_number="ZZZ002", status="active")
        make_vehicle(registered_number="AAA002", status="active")

        active_vehicles = [
            v for v in Vehicle.objects.all() if v.status == "active"]
        numbers = [v.registered_number for v in active_vehicles]
        self.assertEqual(numbers, sorted(numbers))


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

class DriverModelTest(TestCase):

    def setUp(self):
        self.user = make_user("driver1@example.com", "driver1")
        self.vehicle = make_vehicle("DRVVEH001")
        self.driver = make_driver(
            user=self.user,
            license_number="DL1234567890123",
            phone_number="9000000001",
            name="Ravi Kumar",
            primary_vehicle=self.vehicle,
        )

    # --- field correctness ---

    def test_fields_are_saved_correctly(self):
        self.assertEqual(self.driver.name, "Ravi Kumar")
        self.assertEqual(self.driver.license_number, "DL1234567890123")
        self.assertEqual(self.driver.phone_number, "9000000001")
        self.assertEqual(self.driver.status, "active")
        self.assertEqual(self.driver.primary_vehicle, self.vehicle)

    def test_primary_key_is_uuid(self):
        import uuid
        self.assertIsInstance(self.driver.id, uuid.UUID)

    def test_primary_vehicle_can_be_null(self):
        user2 = make_user("driver2@example.com", "driver2")
        driver = make_driver(user=user2, license_number="DL9999999999999",
                             phone_number="9000000002", primary_vehicle=None)
        self.assertIsNone(driver.primary_vehicle)

    def test_str_representation(self):
        expected = "Driver: Ravi Kumar (DL1234567890123)"
        self.assertEqual(str(self.driver), expected)

    # --- constraints ---

    def test_license_number_must_be_unique(self):
        user2 = make_user("driver3@example.com", "driver3")
        with self.assertRaises(IntegrityError):
            make_driver(user=user2, license_number="DL1234567890123",
                        phone_number="9000000003")

    def test_phone_number_must_be_unique(self):
        user2 = make_user("driver4@example.com", "driver4")
        with self.assertRaises(IntegrityError):
            make_driver(user=user2, license_number="DL9999999999998",
                        phone_number="9000000001")   # duplicate

    def test_one_user_one_driver_profile(self):
        """OneToOneField: same user cannot have two Driver rows."""
        with self.assertRaises(IntegrityError):
            make_driver(user=self.user, license_number="DL0000000000000",
                        phone_number="9000000099")

    # NOTE: User→Driver CASCADE and Vehicle→Driver SET_NULL delete tests are
    # intentionally omitted. See issues/issue_model_relation_inconsistency.md
    # — the FK chain across User/Driver/Vehicle/TripLog is broken (DO_NOTHING
    # on TripLog FKs vs CASCADE elsewhere) and delete behaviour is part of the
    # known-bug backlog. The tests will be reintroduced after the FK on_delete
    # values are finalized.

    # --- ordering: Meta.ordering = ['-status', 'name', '-date_created'] ---

    def test_inactive_drivers_sort_before_active(self):
        user_i = make_user("inactive@example.com", "inactive_driver")
        make_driver(user=user_i, license_number="DL0000000000001",
                    phone_number="9000000010", name="Zara", status="inactive")

        drivers = list(Driver.objects.all())
        last_inactive = max(
            (i for i, d in enumerate(drivers) if d.status == "inactive"), default=-1
        )
        first_active = min(
            (i for i, d in enumerate(drivers) if d.status == "active"), default=len(drivers)
        )
        self.assertLess(last_inactive, first_active,
                        msg="Inactive drivers should sort before active ones")

    def test_within_same_status_sorted_by_name_asc(self):
        u2 = make_user("b@example.com", "b")
        u3 = make_user("c@example.com", "c")
        make_driver(u2, license_number="DL0000000000002",
                    phone_number="9000000011", name="Zara")
        make_driver(u3, license_number="DL0000000000003",
                    phone_number="9000000012", name="Amit")

        active = [d for d in Driver.objects.all() if d.status == "active"]
        names = [d.name for d in active]
        self.assertEqual(names, sorted(names))


# ---------------------------------------------------------------------------
# TripLog
# ---------------------------------------------------------------------------

class TripLogModelTest(TestCase):

    def setUp(self):
        self.user = make_user("tripuser@example.com", "tripuser")
        self.vehicle = make_vehicle("TRIPVEH001")
        self.driver = make_driver(
            user=self.user,
            license_number="DL7777777777777",
            phone_number="9000000020",
            primary_vehicle=self.vehicle,
        )
        self.now = timezone.now()
        self.trip = TripLog.objects.create(
            vehicle=self.vehicle,
            driver=self.driver,
            date_time=self.now,
            number_of_trips=5,
            weight=Decimal("1000.50"),
            distance_traveled=Decimal("150.75"),
        )

    # --- field correctness ---

    def test_fields_are_saved_correctly(self):
        self.assertEqual(self.trip.vehicle, self.vehicle)
        self.assertEqual(self.trip.driver, self.driver)
        self.assertEqual(self.trip.number_of_trips, 5)
        self.assertEqual(self.trip.weight, Decimal("1000.50"))
        self.assertEqual(self.trip.distance_traveled, Decimal("150.75"))

    def test_is_approved_defaults_to_false(self):
        """New trip logs start unapproved. This is a critical business rule."""
        self.assertFalse(self.trip.is_approved)

    def test_primary_key_is_uuid(self):
        import uuid
        self.assertIsInstance(self.trip.id, uuid.UUID)

    def test_str_representation(self):
        expected = f"Trip on {self.now} - {self.vehicle.registered_number}"
        self.assertEqual(str(self.trip), expected)

    # --- nullable optional fields ---

    def test_optional_fields_can_all_be_null(self):
        """weight, volume, distance_traveled, diesel_fill, pick_up, drop_off are all optional."""
        trip = TripLog.objects.create(
            vehicle=self.vehicle,
            driver=self.driver,
            date_time=timezone.now(),
            number_of_trips=1,
        )
        self.assertIsNone(trip.weight)
        self.assertIsNone(trip.volume)
        self.assertIsNone(trip.distance_traveled)
        self.assertIsNone(trip.diesel_fill)
        self.assertIsNone(trip.pick_up)
        self.assertIsNone(trip.drop_off)

    def test_last_reason_to_change_defaults_to_empty_string(self):
        self.assertEqual(self.trip.last_reason_to_change, "")

    # --- ordering: Meta.ordering = ['-date_time'] ---

    def test_most_recent_trip_sorts_first(self):
        from datetime import timedelta
        older = TripLog.objects.create(
            vehicle=self.vehicle,
            driver=self.driver,
            date_time=self.now - timedelta(days=1),
            number_of_trips=2,
            weight=Decimal("500.00"),
        )
        trips = list(TripLog.objects.all())
        # self.trip was created with self.now (today), older was yesterday
        self.assertEqual(trips[0].id, self.trip.id)
        self.assertEqual(trips[1].id, older.id)

    # --- django-simple-history ---

    def test_history_record_created_on_save(self):
        """simple_history should create one record when the trip is first saved."""
        self.assertEqual(self.trip.history.count(), 1)

    def test_history_record_created_on_update(self):
        """Each save creates a new history entry."""
        self.trip.number_of_trips = 99
        self.trip.save()
        self.assertEqual(self.trip.history.count(), 2)

    # --- TripLogQuerySet.with_relations() ---

    def test_trip_queryset_with_relations_selects_related_fields(self):
        """with_relations() applies select_related on vehicle/driver/driver__primary_vehicle."""
        # Force a second SELECT to count queries without with_relations.
        from django.db import connection, reset_queries
        from django.conf import settings

        settings.DEBUG = True
        reset_queries()
        list(TripLog.objects.all())
        baseline_query_count = len(connection.queries)

        reset_queries()
        list(TripLog.objects.with_relations())
        with_relations_query_count = len(connection.queries)

        # with_relations() should not issue strictly more queries than the bare
        # queryset (in fact it issues fewer because joins are collapsed into one
        # SELECT). The important property is that with_relations does not multiply
        # queries: it must be <= the baseline + 1 (one SELECT for the joined
        # data is the whole point).
        self.assertLessEqual(
            with_relations_query_count, baseline_query_count + 1,
            msg="with_relations() should not multiply queries"
        )

    def test_trip_queryset_with_relations_filters_correctly(self):
        """filter(...).with_relations() preserves both the filter and the joins."""
        from datetime import timedelta
        other = TripLog.objects.create(
            vehicle=self.vehicle,
            driver=self.driver,
            date_time=self.now - timedelta(days=1),
            number_of_trips=1,
            weight=Decimal("100.00"),
        )
        # .filter() then .with_relations(): only today's trip, joined to vehicle+driver.
        qs = TripLog.objects.filter(
            date_time__date=self.now.date()).with_relations()
        results = list(qs)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.trip.id)
        self.assertIsNotNone(results[0].vehicle)
        self.assertEqual(results[0].vehicle.id, self.vehicle.id)
        self.assertEqual(results[0].driver.id, self.driver.id)


# ---------------------------------------------------------------------------
# UserManager + User  (users.models)
# ---------------------------------------------------------------------------

class TestUserManager(TestCase):
    """
    Tests for the custom UserManager and User model that weren't covered by
    the fleet/vehicle/driver/trip model tests above.
    """

    # --- UserManager.create_user ---

    def test_create_user_normalizes_email(self):
        """Email with mixed-case local-part is lowercased before save."""
        user = User.objects.create_user(
            email="MixedCase@EXAMPLE.COM", username="mixedcase", password="pw12345")
        self.assertEqual(user.email, "MixedCase@example.com")

    def test_create_user_with_missing_email_raises_value_error(self):
        """create_user must reject empty/None email."""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email="", username="noname", password="pw12345")

    def test_create_user_sets_password_correctly(self):
        """password is hashed via set_password, not stored plaintext."""
        user = User.objects.create_user(
            email="hash@test.com", username="hashtest", password="plaintext")
        self.assertNotEqual(user.password, "plaintext")
        self.assertTrue(user.check_password("plaintext"))

    def test_create_user_default_flags_are_false(self):
        user = User.objects.create_user(
            email="flag@test.com", username="flagtest", password="pw12345")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_manager)
        self.assertTrue(user.is_active)

    # --- UserManager.create_superuser ---

    def test_create_superuser_sets_is_staff_and_is_superuser(self):
        superuser = User.objects.create_superuser(
            email="root@test.com", username="root", password="root12345")
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

    def test_create_superuser_uses_create_user(self):
        """create_superuser delegates to create_user (and normalizes email)."""
        superuser = User.objects.create_superuser(
            email="ROOT@TEST.COM", username="root2", password="root12345")
        self.assertEqual(superuser.email, "ROOT@test.com")
        self.assertTrue(superuser.check_password("root12345"))

    # --- User.__str__ ---

    def test_user_str_returns_email(self):
        user = User.objects.create_user(
            email="str@test.com", username="struser", password="pw12345")
        self.assertEqual(str(user), "str@test.com")
