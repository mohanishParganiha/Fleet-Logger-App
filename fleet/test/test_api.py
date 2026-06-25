"""
API / integration tests for the fleet app.

PHILOSOPHY:
  Each test follows the AAA pattern:
    Arrange  – set up state (users, objects, auth)
    Act      – make the HTTP request
    Assert   – check status code AND meaningful response data

  We never use time.sleep(). When testing time-sensitive behaviour we use
  unittest.mock.patch to freeze or advance the clock. sleep() makes test
  suites painfully slow and flaky.

  We use force_authenticate() instead of posting to /login/ in every test.
  force_authenticate() bypasses the auth mechanism and is the DRF-recommended
  way to focus a test on permissions/logic rather than on login flow.
  The login/logout flow gets its own dedicated AuthenticationTest class.

COVERAGE MAP:
  AuthenticationTest      – login, failed login, missing fields, logout, cookie auth
  VehicleAPITest          – CRUD, permissions, filtering, pagination
  DriverAPITest           – CRUD, permissions, nested-user creation
  TripLogAPITest          – CRUD, approval flow, time-window guard, calculation endpoints
  UserAPITest             – retrieve/update/delete via /api/users/<uuid>/
"""

from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from fleet.models import Driver, TripLog, Vehicle

User = get_user_model()


# ---------------------------------------------------------------------------
# Shared factory helpers  (keep setUp methods short and readable)
# ---------------------------------------------------------------------------

def make_user(email, username="user", password="TestPass123", **kwargs):
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
        user=user, name=name, license_number=license_number,
        phone_number=phone_number, status=status, primary_vehicle=primary_vehicle,
    )


def make_trip(vehicle, driver, number_of_trips=5,
              weight="1000.00", distance="100.00", days_ago=0):
    return TripLog.objects.create(
        vehicle=vehicle,
        driver=driver,
        date_time=timezone.now() - timedelta(days=days_ago),
        number_of_trips=number_of_trips,
        weight=Decimal(weight),
        distance_traveled=Decimal(distance),
    )


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

class AuthenticationTest(APITestCase):
    """Tests the /api/login/ and /api/logout/ endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = make_user("auth@test.com", "authuser", "TestPass123")

    # --- login ---

    def test_login_with_valid_credentials_returns_200(self):
        response = self.client.post(
            "/api/login/",
            {"email": "auth@test.com", "password": "TestPass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_sets_httponly_cookie(self):
        response = self.client.post(
            "/api/login/",
            {"email": "auth@test.com", "password": "TestPass123"},
            format="json",
        )
        self.assertIn("auth_token", response.cookies)
        self.assertTrue(response.cookies["auth_token"]["httponly"])

    def test_login_returns_user_metadata(self):
        response = self.client.post(
            "/api/login/",
            {"email": "auth@test.com", "password": "TestPass123"},
            format="json",
        )
        self.assertIn("email", response.data)
        self.assertIn("is_staff", response.data)
        self.assertIn("is_manager", response.data)
        # token must NOT be in the JSON body — it lives in the cookie
        self.assertNotIn("token", response.data)

    def test_login_with_wrong_password_returns_401(self):
        response = self.client.post(
            "/api/login/",
            {"email": "auth@test.com", "password": "WrongPassword"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_with_missing_fields_returns_400(self):
        response = self.client.post(
            "/api/login/", {"email": "auth@test.com"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- cookie-based auth ---

    def test_protected_endpoint_works_with_valid_cookie(self):
        """Simulates what the browser does: sends cookie on subsequent requests."""
        token = Token.objects.create(user=self.user)
        self.client.cookies["auth_token"] = token.key
        response = self.client.get("/api/vehicles/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_protected_endpoint_rejects_request_without_auth(self):
        response = self.client.get("/api/vehicles/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- logout ---

    def test_logout_returns_200(self):
        token = Token.objects.create(user=self.user)
        self.client.cookies["auth_token"] = token.key
        response = self.client.post("/api/logout/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_deletes_token_from_database(self):
        token = Token.objects.create(user=self.user)
        self.client.cookies["auth_token"] = token.key
        self.client.post("/api/logout/")
        self.assertFalse(Token.objects.filter(key=token.key).exists())

    def test_logout_clears_cookie(self):
        token = Token.objects.create(user=self.user)
        self.client.cookies["auth_token"] = token.key
        response = self.client.post("/api/logout/")
        self.assertEqual(response.cookies["auth_token"].value, "")
        self.assertEqual(response.cookies["auth_token"]["max-age"], 0)

    def test_logout_requires_authentication(self):
        """Unauthenticated users cannot hit the logout endpoint."""
        response = self.client.post("/api/logout/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Vehicle
# ---------------------------------------------------------------------------

class VehicleAPITest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.admin = make_user("admin@v.com", "admin",
                               is_staff=True, is_superuser=True)
        self.manager = make_user("manager@v.com", "manager", is_manager=True)
        self.regular = make_user("regular@v.com", "regular")
        self.vehicle = make_vehicle("CG07XY0001")

    def auth(self, user):
        self.client.force_authenticate(user=user)

    # --- list ---

    def test_list_requires_authentication(self):
        response = self.client.get("/api/vehicles/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_200_for_authenticated_user(self):
        self.auth(self.regular)
        response = self.client.get("/api/vehicles/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_is_paginated(self):
        for i in range(11):
            make_vehicle(f"CG07XY{i+10:04d}")
        self.auth(self.regular)
        response = self.client.get("/api/vehicles/")
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIn("next", response.data)

    def test_filter_by_status_inactive(self):
        make_vehicle("CG07ZZINAC", status="inactive")
        self.auth(self.regular)
        response = self.client.get("/api/vehicles/?status=inactive")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            all(v["status"] == "inactive" for v in response.data["results"]))

    def test_filter_by_registered_number(self):
        self.auth(self.regular)
        response = self.client.get(
            "/api/vehicles/?registered_number=CG07XY0001")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"]
                         [0]["registered_number"], "CG07XY0001")

    # --- create ---

    def test_create_as_admin_returns_201(self):
        self.auth(self.admin)
        response = self.client.post(
            "/api/vehicles/",
            {"model": "Tata Ace", "registered_number": "NEWVEH001", "status": "active"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Vehicle.objects.filter(
            registered_number="NEWVEH001").exists())

    def test_create_as_manager_returns_201(self):
        self.auth(self.manager)
        response = self.client.post(
            "/api/vehicles/",
            {"model": "Tata Ace", "registered_number": "NEWVEH002", "status": "active"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_as_regular_user_returns_403(self):
        self.auth(self.regular)
        response = self.client.post(
            "/api/vehicles/",
            {"model": "Tata Ace", "registered_number": "NEWVEH003", "status": "active"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_unauthenticated_returns_401(self):
        response = self.client.post(
            "/api/vehicles/",
            {"model": "Tata Ace", "registered_number": "NEWVEH004", "status": "active"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_with_duplicate_registered_number_returns_400(self):
        self.auth(self.admin)
        response = self.client.post(
            "/api/vehicles/",
            {"model": "Tata Ace", "registered_number": "CG07XY0001"},   # already exists
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- update ---

    def test_update_as_manager_returns_200(self):
        self.auth(self.manager)
        response = self.client.patch(
            f"/api/vehicles/{self.vehicle.id}/",
            {"status": "inactive"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.status, "inactive")

    def test_update_as_regular_user_returns_403(self):
        self.auth(self.regular)
        response = self.client.patch(
            f"/api/vehicles/{self.vehicle.id}/",
            {"status": "inactive"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- delete ---

    def test_delete_as_admin_returns_204(self):
        self.auth(self.admin)
        response = self.client.delete(f"/api/vehicles/{self.vehicle.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Vehicle.objects.filter(id=self.vehicle.id).exists())

    def test_delete_as_manager_returns_403(self):
        self.auth(self.manager)
        response = self.client.delete(f"/api/vehicles/{self.vehicle.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_detail_unauthenticated_returns_401(self):
        response = self.client.get(f"/api/vehicles/{self.vehicle.id}/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

class DriverAPITest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.admin = make_user("admin@d.com", "admin_d",
                               is_staff=True, is_superuser=True)
        self.manager = make_user("manager@d.com", "manager_d", is_manager=True)
        self.regular = make_user("regular@d.com", "regular_d")

        self.vehicle = make_vehicle("DRVVEH001")
        self.driver_user = make_user("driver@d.com", "driver_d")
        self.driver = make_driver(
            self.driver_user,
            license_number="DL1111111111111",
            phone_number="9100000001",
            name="Existing Driver",
            primary_vehicle=self.vehicle,
        )

    def auth(self, user):
        self.client.force_authenticate(user=user)

    def _create_driver_payload(self, email="new@d.com", username="newdrv",
                               license="DL9999999999999", phone="9100009999"):
        return {
            "user": {"email": email, "username": username, "password": "NewPass123"},
            "name": "New Driver",
            "phone_number": phone,
            "license_number": license,
            "primary_vehicle": str(self.vehicle.id),
            "status": "active",
        }

    # --- list ---

    def test_list_requires_authentication(self):
        response = self.client.get("/api/drivers/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_200_for_authenticated_user(self):
        self.auth(self.regular)
        response = self.client.get("/api/drivers/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # --- create ---

    def test_create_as_manager_returns_201(self):
        self.auth(self.manager)
        response = self.client.post(
            "/api/drivers/", self._create_driver_payload(), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_also_creates_user_account(self):
        """DriverSerializer.create() must create both a Driver and a User atomically."""
        self.auth(self.manager)
        payload = self._create_driver_payload(
            email="linked@d.com", username="linked_user", license="DL8888888888888", phone="9100008888"
        )
        self.client.post("/api/drivers/", payload, format="json")
        self.assertTrue(User.objects.filter(email="linked@d.com").exists())

    def test_create_as_admin_returns_201(self):
        self.auth(self.admin)
        response = self.client.post(
            "/api/drivers/",
            self._create_driver_payload(
                email="admin_created@d.com", username="admin_drv",
                license="DL7777777777777", phone="9100007777"
            ),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_as_regular_user_returns_403(self):
        self.auth(self.regular)
        response = self.client.post(
            "/api/drivers/", self._create_driver_payload(), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_with_duplicate_license_number_returns_400(self):
        self.auth(self.admin)
        payload = self._create_driver_payload(
            email="dup@d.com", username="dup_drv",
            license="DL1111111111111",   # duplicate
            phone="9100006666"
        )
        response = self.client.post("/api/drivers/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- update ---

    def test_update_as_manager_returns_200(self):
        self.auth(self.manager)
        response = self.client.patch(
            f"/api/drivers/{self.driver.id}/",
            {"status": "inactive"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.driver.refresh_from_db()
        self.assertEqual(self.driver.status, "inactive")

    def test_update_as_regular_user_returns_403(self):
        self.auth(self.regular)
        response = self.client.patch(
            f"/api/drivers/{self.driver.id}/",
            {"status": "inactive"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- delete ---

    def test_delete_as_admin_returns_204(self):
        self.auth(self.admin)
        response = self.client.delete(f"/api/drivers/{self.driver.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Driver.objects.filter(id=self.driver.id).exists())

    def test_delete_as_manager_returns_403(self):
        self.auth(self.manager)
        response = self.client.delete(f"/api/drivers/{self.driver.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# TripLog
# ---------------------------------------------------------------------------

class TripLogAPITest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.admin = make_user("admin@t.com", "admin_t",
                               is_staff=True, is_superuser=True)
        self.manager = make_user("manager@t.com", "manager_t", is_manager=True)
        self.regular = make_user("regular@t.com", "regular_t")
        self.driver_user = make_user("driver@t.com", "driver_t")

        self.vehicle = make_vehicle("TRIPVEH001")
        self.driver = make_driver(
            self.driver_user,
            license_number="DL2222222222222",
            phone_number="9200000001",
            name="Trip Driver",
            primary_vehicle=self.vehicle,
        )
        self.trip = make_trip(self.vehicle, self.driver)

    def auth(self, user):
        self.client.force_authenticate(user=user)

    def _create_trip_payload(self, vehicle_number=None, **overrides):
        payload = {
            "driver": self.driver.license_number,
            "date_time": timezone.now().isoformat(),
            "number_of_trips": 3,
            "weight": "500.00",
            "distance_traveled": "75.00",
        }
        if vehicle_number:
            payload["vehicle"] = vehicle_number
        payload.update(overrides)
        return payload

    # --- list ---

    def test_list_requires_authentication(self):
        response = self.client.get("/api/trip-logs/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_200_and_nested_vehicle_for_authenticated_user(self):
        self.auth(self.regular)
        response = self.client.get("/api/trip-logs/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # to_representation nests the vehicle object — verify the structure
        result = response.data["results"][0]
        self.assertIsInstance(result["vehicle"], dict)
        self.assertEqual(result["vehicle"]["registered_number"], "TRIPVEH001")

    def test_list_filter_by_vehicle_registered_number(self):
        other_vehicle = make_vehicle("FILTERVEH1")
        other_driver_user = make_user("od@t.com", "od_t")
        other_driver = make_driver(
            other_driver_user, license_number="DL3333333333333",
            phone_number="9200000002", primary_vehicle=other_vehicle
        )
        make_trip(other_vehicle, other_driver)

        self.auth(self.regular)
        response = self.client.get("/api/trip-logs/?vehicle=FILTERVEH1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["vehicle"]["registered_number"], "FILTERVEH1"
        )

    def test_list_filter_by_date_range(self):
        make_trip(self.vehicle, self.driver, days_ago=5)   # outside range
        self.auth(self.regular)
        today = timezone.now().date().isoformat()
        response = self.client.get(
            f"/api/trip-logs/?start_date={today}&end_date={today}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only today's trip should appear
        self.assertEqual(len(response.data["results"]), 1)

    # --- create ---

    def test_create_as_authenticated_user_returns_201(self):
        self.auth(self.regular)
        response = self.client.post(
            "/api/trip-logs/", self._create_trip_payload(), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TripLog.objects.count(), 2)

    def test_create_unauthenticated_returns_401(self):
        response = self.client.post(
            "/api/trip-logs/", self._create_trip_payload(), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_without_weight_or_volume_returns_400(self):
        """Serializer validate() requires at least weight OR volume."""
        self.auth(self.regular)
        payload = {
            "driver": self.driver.license_number,
            "date_time": timezone.now().isoformat(),
            "number_of_trips": 3,
            # no weight, no volume
        }
        response = self.client.post("/api/trip-logs/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_without_vehicle_defaults_to_driver_primary_vehicle(self):
        """When no vehicle is sent, the serializer should fall back to driver.primary_vehicle."""
        self.auth(self.regular)
        response = self.client.post(
            "/api/trip-logs/", self._create_trip_payload(), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        trip_id = response.data["id"]
        trip = TripLog.objects.get(id=trip_id)
        self.assertEqual(trip.vehicle, self.driver.primary_vehicle)

    def test_create_with_explicit_vehicle_override_saves_that_vehicle(self):
        """Manager can assign a different vehicle than the driver's primary one."""
        override_vehicle = make_vehicle("RIDE001")
        self.auth(self.manager)
        response = self.client.post(
            "/api/trip-logs/",
            self._create_trip_payload(vehicle_number="RIDE001"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        trip = TripLog.objects.get(id=response.data["id"])
        self.assertEqual(trip.vehicle, override_vehicle)

    # --- detail ---

    def test_detail_returns_nested_driver_and_vehicle(self):
        self.auth(self.regular)
        response = self.client.get(f"/api/trip-logs/{self.trip.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data["driver"], dict)
        self.assertIsInstance(response.data["vehicle"], dict)

    # --- update ---

    def test_update_as_manager_with_reason_returns_200(self):
        self.auth(self.manager)
        response = self.client.patch(
            f"/api/trip-logs/{self.trip.id}/",
            {"number_of_trips": 9, "last_reason_to_change": "Correcting entry error"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.trip.refresh_from_db()
        self.assertEqual(self.trip.number_of_trips, 9)

    def test_update_without_reason_returns_400(self):
        """Serializer rejects any PUT/PATCH that lacks last_reason_to_change."""
        self.auth(self.manager)
        response = self.client.patch(
            f"/api/trip-logs/{self.trip.id}/",
            {"number_of_trips": 9},   # no reason provided
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_driver_can_update_own_trip_within_time_window(self):
        """
        A regular (driver-role) user can edit a trip they just created,
        as long as it is within the allowed time window.
        We keep the trip fresh (just created in setUp) so we're inside the window.
        """
        self.auth(self.driver_user)
        response = self.client.patch(
            f"/api/trip-logs/{self.trip.id}/",
            {
                "number_of_trips": 7,
                "last_reason_to_change": "Fixing count",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_driver_cannot_update_trip_outside_time_window(self):
        """
        We mock timezone.now() to return a time 3 hours AFTER the trip was created.
        This pushes the elapsed time past the 2-hour window, triggering the 400.

        WHY MOCK INSTEAD OF sleep():
          sleep(7200) would make this test take 2 hours.
          Mocking lets us simulate any point in time instantly.
        """
        self.auth(self.driver_user)
        # Patch timezone.now in the serializers module where it is actually called
        future_time = timezone.now() + timedelta(hours=3)
        with patch("fleet.serializers.timezone.now", return_value=future_time):
            response = self.client.patch(
                f"/api/trip-logs/{self.trip.id}/",
                {
                    "number_of_trips": 7,
                    "last_reason_to_change": "Too late",
                },
                format="json",
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_driver_cannot_update_approved_trip(self):
        """Once a trip is approved (locked), even a timely edit by a driver must be rejected."""
        # Approve the trip first
        self.trip.is_approved = True
        self.trip.save()

        self.auth(self.driver_user)
        response = self.client.patch(
            f"/api/trip-logs/{self.trip.id}/",
            {
                "number_of_trips": 7,
                "last_reason_to_change": "Should not work",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- approve ---

    def test_approve_as_admin_returns_200_and_locks_trip(self):
        self.auth(self.admin)
        response = self.client.post(f"/api/trip-logs/{self.trip.id}/approve/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.trip.refresh_from_db()
        self.assertTrue(self.trip.is_approved)

    def test_approve_as_manager_returns_200(self):
        self.auth(self.manager)
        response = self.client.post(f"/api/trip-logs/{self.trip.id}/approve/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_approve_already_approved_trip_returns_400(self):
        """Approving twice should be rejected to prevent redundant DB writes."""
        self.auth(self.admin)
        # first approve
        self.client.post(f"/api/trip-logs/{self.trip.id}/approve/")
        response = self.client.post(
            f"/api/trip-logs/{self.trip.id}/approve/")   # second
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_approve_as_regular_user_returns_403(self):
        self.auth(self.regular)
        response = self.client.post(f"/api/trip-logs/{self.trip.id}/approve/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_approve_nonexistent_trip_returns_404(self):
        self.auth(self.admin)
        import uuid
        fake_id = uuid.uuid4()
        response = self.client.post(f"/api/trip-logs/{fake_id}/approve/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- delete ---

    def test_delete_as_admin_returns_204(self):
        self.auth(self.admin)
        response = self.client.delete(f"/api/trip-logs/{self.trip.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TripLog.objects.filter(id=self.trip.id).exists())

    def test_delete_as_regular_user_returns_403(self):
        self.auth(self.regular)
        response = self.client.delete(f"/api/trip-logs/{self.trip.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- single-trip calculation ---

    def test_calculate_weight_as_manager_returns_correct_amount(self):
        # amount = number_of_trips * weight * rate = 5 * 1000 * 10.50 = 52500
        self.auth(self.manager)
        response = self.client.post(
            f"/api/trip-logs/{self.trip.id}/calculate/",
            {"rate": "10.50", "calc_type": "weight"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = float(Decimal("1000.00") * 5 * Decimal("10.50"))
        self.assertAlmostEqual(response.data["amount"], expected, places=2)

    def test_calculate_distance_as_manager_returns_correct_amount(self):
        # amount = 5 * 100 * 2 = 1000
        self.auth(self.manager)
        response = self.client.post(
            f"/api/trip-logs/{self.trip.id}/calculate/",
            {"rate": "2", "calc_type": "distance"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = float(Decimal("100.00") * 5 * Decimal("2"))
        self.assertAlmostEqual(response.data["amount"], expected, places=2)

    def test_calculate_with_invalid_calc_type_returns_400(self):
        self.auth(self.manager)
        response = self.client.post(
            f"/api/trip-logs/{self.trip.id}/calculate/",
            {"rate": "10", "calc_type": "volume"},   # invalid
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_calculate_with_missing_rate_returns_400(self):
        self.auth(self.manager)
        response = self.client.post(
            f"/api/trip-logs/{self.trip.id}/calculate/",
            {"calc_type": "weight"},   # no rate
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_calculate_requires_manager_or_admin(self):
        self.auth(self.regular)
        response = self.client.post(
            f"/api/trip-logs/{self.trip.id}/calculate/",
            {"rate": "10", "calc_type": "weight"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- bulk calculation ---

    def test_bulk_calculate_weight_as_manager_returns_correct_total(self):
        # Add a second trip so we can verify aggregation
        make_trip(self.vehicle, self.driver,
                  number_of_trips=2, weight="500.00")
        self.auth(self.manager)
        today = timezone.now().date().isoformat()
        response = self.client.post(
            "/api/trip-logs/calculate-bulk/",
            {
                "start_date": today,
                "end_date": today,
                "rate": "5",
                "calc_type": "weight",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_amount", response.data)
        self.assertIn("total_weight", response.data)
        self.assertGreater(response.data["total_amount"], 0)

    def test_bulk_calculate_with_vehicle_filter(self):
        other_vehicle = make_vehicle("BULKVEH002")
        other_driver_user = make_user("bv@t.com", "bv_t")
        other_driver = make_driver(
            other_driver_user, license_number="DL5555555555555",
            phone_number="9200000099", primary_vehicle=other_vehicle
        )
        make_trip(other_vehicle, other_driver, weight="9999.00")

        self.auth(self.manager)
        today = timezone.now().date().isoformat()
        response = self.client.post(
            "/api/trip-logs/calculate-bulk/",
            {
                "start_date": today,
                "end_date": today,
                "rate": "5",
                "calc_type": "weight",
                "vehicle": "TRIPVEH001",   # filter to only self.vehicle
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The other vehicle's 9999kg trip must NOT be in the total
        self.assertEqual(response.data["vehicle"], "TRIPVEH001")
        # total_weight should only reflect TRIPVEH001 trips
        self.assertLess(response.data["total_weight"], 9999.0)

    def test_bulk_calculate_with_invalid_date_format_returns_400(self):
        self.auth(self.manager)
        response = self.client.post(
            "/api/trip-logs/calculate-bulk/",
            {
                "start_date": "01-01-2025",   # wrong format
                "end_date": "2025-01-10",
                "rate": "5",
                "calc_type": "weight",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_bulk_calculate_with_start_after_end_returns_400(self):
        self.auth(self.manager)
        response = self.client.post(
            "/api/trip-logs/calculate-bulk/",
            {
                "start_date": "2025-12-01",
                "end_date": "2025-01-01",   # start > end
                "rate": "5",
                "calc_type": "weight",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_calculate_as_regular_user_returns_403(self):
        self.auth(self.regular)
        today = timezone.now().date().isoformat()
        response = self.client.post(
            "/api/trip-logs/calculate-bulk/",
            {"start_date": today, "end_date": today,
                "rate": "5", "calc_type": "weight"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_bulk_calculate_with_nonexistent_vehicle_returns_404(self):
        self.auth(self.manager)
        today = timezone.now().date().isoformat()
        response = self.client.post(
            "/api/trip-logs/calculate-bulk/",
            {
                "start_date": today,
                "end_date": today,
                "rate": "5",
                "calc_type": "weight",
                "vehicle": "GHOST999",   # doesn't exist
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# User (via /api/users/<uuid:pk>/)
# ---------------------------------------------------------------------------

class UserAPITest(APITestCase):
    """
    Tests for UpdateUser view (RetrieveUpdateDestroyAPIView).
    Endpoint: /api/users/<uuid>/

    NOTE: There is no /api/users/create/ endpoint.
    User creation happens via the nested payload in DriverSerializer.
    """

    def setUp(self):
        self.client = APIClient()
        self.admin = make_user("admin@u.com", "admin_u",
                               is_staff=True, is_superuser=True)
        self.manager = make_user("manager@u.com", "manager_u", is_manager=True)
        self.regular = make_user("regular@u.com", "regular_u")

    def auth(self, user):
        self.client.force_authenticate(user=user)

    # --- retrieve ---

    def test_admin_can_retrieve_any_user(self):
        self.auth(self.admin)
        response = self.client.get(f"/api/users/{self.regular.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.regular.email)

    def test_manager_can_retrieve_any_user(self):
        self.auth(self.manager)
        response = self.client.get(f"/api/users/{self.regular.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_retrieve_other_users(self):
        self.auth(self.regular)
        response = self.client.get(f"/api/users/{self.admin.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_retrieve_user(self):
        response = self.client.get(f"/api/users/{self.regular.id}/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- update ---

    def test_admin_can_update_user(self):
        self.auth(self.admin)
        response = self.client.patch(
            f"/api/users/{self.regular.id}/",
            {"username": "updated_name"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular.refresh_from_db()
        self.assertEqual(self.regular.username, "updated_name")

    def test_manager_can_update_user(self):
        self.auth(self.manager)
        response = self.client.patch(
            f"/api/users/{self.regular.id}/",
            {"username": "manager_updated"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_update_users(self):
        self.auth(self.regular)
        response = self.client.patch(
            f"/api/users/{self.regular.id}/",
            {"username": "self_update"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- delete ---

    def test_admin_can_delete_user(self):
        target = make_user("delete_me@u.com", "delete_me_u")
        self.auth(self.admin)
        response = self.client.delete(f"/api/users/{target.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=target.id).exists())
