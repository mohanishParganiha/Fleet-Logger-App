"""
API / integration tests for the fleet app (v1).

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
  VehicleAPITest          – CRUD, permissions, filtering, pagination (PBAC)
  DriverAPITest           – CRUD, permissions, nested-user creation, destroy-override
  DriverMeAPITest         – self-service /drivers/me (GET, PATCH, DELETE)
  TripLogAPITest          – CRUD, approval flow, time-window guard, calculation endpoints, role-based queryset
  UserAPITest             – retrieve/delete via /api/users/<uuid>/, /users/ list, PATCH now 405
  UserChangePasswordAPITest – /users/me/change-password/ validation and DB update

All endpoints are versioned under /api/v1/.
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


def make_manager(email, username="manager", password="TestPass123"):
    """Convenience helper for a manager-flagged user."""
    return User.objects.create_user(
        email=email, username=username, password=password, is_manager=True
    )


def make_driver_user_with_profile(
    email, username, password="TestPass123",
    license_number="DL0000000", phone_number="9000000000",
    name="Driver Name", primary_vehicle=None,
):
    """One-shot helper that creates a User AND its linked Driver profile."""
    user = make_user(email, username, password)
    return user, make_driver(
        user=user,
        license_number=license_number,
        phone_number=phone_number,
        name=name,
        primary_vehicle=primary_vehicle,
    )


def make_trip(vehicle, driver, number_of_trips=5,
              weight="1000.00", distance="100.00", volume=None, days_ago=0):
    data = {
        'vehicle': vehicle,
        'driver': driver,
        'date_time': timezone.now() - timedelta(days=days_ago),
        'number_of_trips': number_of_trips,
        'weight': Decimal(weight),
        'distance_traveled': Decimal(distance),
    }
    if volume is not None:
        data['volume'] = Decimal(volume)
    return TripLog.objects.create(**data)


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

class AuthenticationTest(APITestCase):
    """Tests the /api/v1/login/ and /api/v1/logout/ endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = make_user("auth@test.com", "authuser", "TestPass123")

    # --- login ---

    def test_login_with_valid_credentials_returns_200(self):
        response = self.client.post(
            "/api/v1/login/",
            {"email": "auth@test.com", "password": "TestPass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_sets_httponly_cookie(self):
        response = self.client.post(
            "/api/v1/login/",
            {"email": "auth@test.com", "password": "TestPass123"},
            format="json",
        )
        self.assertIn("auth_token", response.cookies)
        self.assertTrue(response.cookies["auth_token"]["httponly"])

    def test_login_returns_user_metadata(self):
        response = self.client.post(
            "/api/v1/login/",
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
            "/api/v1/login/",
            {"email": "auth@test.com", "password": "WrongPassword"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_with_missing_fields_returns_400(self):
        response = self.client.post(
            "/api/v1/login/", {"email": "auth@test.com"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- cookie-based auth ---
# problem here , 404 != 200.
    def test_protected_endpoint_works_with_valid_cookie(self):
        """Simulates what the browser does: sends cookie on subsequent requests."""
        token = Token.objects.create(user=self.user)
        self.client.cookies["auth_token"] = token.key
        response = self.client.get(f"/api/v1/users/{self.user.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_protected_endpoint_rejects_request_without_auth(self):
        response = self.client.get("/api/v1/vehicles/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- logout ---

    def test_logout_returns_200(self):
        token = Token.objects.create(user=self.user)
        self.client.cookies["auth_token"] = token.key
        response = self.client.post("/api/v1/logout/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_deletes_token_from_database(self):
        token = Token.objects.create(user=self.user)
        self.client.cookies["auth_token"] = token.key
        self.client.post("/api/v1/logout/")
        self.assertFalse(Token.objects.filter(key=token.key).exists())

    def test_logout_clears_cookie(self):
        token = Token.objects.create(user=self.user)
        self.client.cookies["auth_token"] = token.key
        response = self.client.post("/api/v1/logout/")
        self.assertEqual(response.cookies["auth_token"].value, "")
        self.assertEqual(response.cookies["auth_token"]["max-age"], 0)

    def test_logout_requires_authentication(self):
        """Unauthenticated users cannot hit the logout endpoint."""
        response = self.client.post("/api/v1/logout/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Vehicle
# ---------------------------------------------------------------------------

class VehicleAPITest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.admin = make_user("admin@v.com", "admin",
                               is_staff=True, is_superuser=True)
        self.manager = make_manager("manager@v.com", "manager")
        # Driver user: has a Driver profile with primary_vehicle → sees ONLY
        # that vehicle in the list endpoint.
        self.driver_user, self.driver = make_driver_user_with_profile(
            email="driver@v.com", username="driver_v",
            license_number="DL1111111111111",
            phone_number="9000000001",
            name="Vehicle Driver",
        )
        self.regular = make_user("regular@v.com", "regular")
        self.vehicle = make_vehicle("CG07XY0001")
        # Make the driver's primary_vehicle point at our test vehicle so the
        # list-as-driver tests have a meaningful expected value.
        self.driver.primary_vehicle = self.vehicle
        self.driver.save()
        # A second vehicle that must NOT appear when the driver lists.
        self.other_vehicle = make_vehicle("CG07XX9999")

    def auth(self, user):
        self.client.force_authenticate(user=user)

    # --- list ---

    def test_list_requires_authentication(self):
        response = self.client.get("/api/v1/vehicles/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_as_regular_user_with_driver_profile_sees_only_own_primary_vehicle(self):
        """A regular user with a Driver profile must see ONLY their primary vehicle."""
        self.auth(self.driver_user)
        response = self.client.get("/api/v1/vehicles/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["registered_number"],
                         self.vehicle.registered_number)

    def test_list_as_manager_sees_all_vehicles(self):
        """A manager sees every vehicle, ignoring the driver-scoping rule."""
        self.auth(self.manager)
        response = self.client.get("/api/v1/vehicles/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        registered_numbers = {v["registered_number"]
                              for v in response.data["results"]}
        self.assertIn(self.vehicle.registered_number, registered_numbers)
        self.assertIn(self.other_vehicle.registered_number, registered_numbers)

    def test_list_is_paginated(self):
        """Pagination kicks in after 10 rows. Authenticate as a manager so all
        rows are visible (regular-with-profile would only ever see one)."""
        for i in range(11):
            make_vehicle(f"CG07XY{i + 10:04d}")
        self.auth(self.manager)
        response = self.client.get("/api/v1/vehicles/")
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIn("next", response.data)

    def test_filter_by_status_inactive(self):
        make_vehicle("CG07ZZINAC", status="inactive")
        self.auth(self.manager)
        response = self.client.get("/api/v1/vehicles/?status=inactive")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            all(v["status"] == "inactive" for v in response.data["results"]))

    def test_filter_by_registered_number(self):
        self.auth(self.manager)
        response = self.client.get(
            "/api/v1/vehicles/?registered_number=CG07XY0001"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"]
                         [0]["registered_number"], "CG07XY0001")

    def test_pagination_first_page(self):
        """Test pagination with page parameter."""
        for i in range(15):
            make_vehicle(f"PAGE{i + 10:04d}")
        self.auth(self.manager)
        response = self.client.get("/api/v1/vehicles/?page=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIn("count", response.data)
        self.assertEqual(response.data["count"], 17)

    def test_pagination_last_page(self):
        """Test pagination on last page."""
        for i in range(13):
            make_vehicle(f"PAGEX{i + 10:04d}")
        self.auth(self.manager)
        response = self.client.get("/api/v1/vehicles/?page=2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 5)
        self.assertIn("count", response.data)
        self.assertEqual(response.data["count"], 15)

    def test_pagination_page_size(self):
        """Test custom page size."""
        for i in range(20):
            make_vehicle(f"PAGEX{i + 10:04d}")
        self.auth(self.manager)
        response = self.client.get("/api/v1/vehicles/?page=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIn("count", response.data)
        self.assertEqual(response.data["count"], 22)

    # --- create ---

    def test_create_as_admin_returns_201(self):
        self.auth(self.admin)
        response = self.client.post(
            "/api/v1/vehicles/",
            {"model": "Tata Ace", "registered_number": "NEWVEH001", "status": "active"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Vehicle.objects.filter(
            registered_number="NEWVEH001").exists())

    def test_create_as_manager_returns_201(self):
        self.auth(self.manager)
        response = self.client.post(
            "/api/v1/vehicles/",
            {"model": "Tata Ace", "registered_number": "NEWVEH002", "status": "active"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_as_regular_user_returns_403(self):
        self.auth(self.regular)
        response = self.client.post(
            "/api/v1/vehicles/",
            {"model": "Tata Ace", "registered_number": "NEWVEH003", "status": "active"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_unauthenticated_returns_401(self):
        response = self.client.post(
            "/api/v1/vehicles/",
            {"model": "Tata Ace", "registered_number": "NEWVEH004", "status": "active"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_with_duplicate_registered_number_returns_400(self):
        self.auth(self.admin)
        response = self.client.post(
            "/api/v1/vehicles/",
            {"model": "Tata Ace", "registered_number": "CG07XY0001"},   # already exists
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- update ---

    def test_update_as_manager_returns_200(self):
        self.auth(self.manager)
        response = self.client.patch(
            f"/api/v1/vehicles/{self.vehicle.id}/",
            {"status": "inactive"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.status, "inactive")

    def test_update_as_regular_user_returns_403(self):
        self.auth(self.regular)
        response = self.client.patch(
            f"/api/v1/vehicles/{self.vehicle.id}/",
            {"status": "inactive"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_as_regular_user_with_put_returns_403(self):
        """Same as PATCH but using PUT — must also be 403."""
        self.auth(self.regular)
        response = self.client.put(
            f"/api/v1/vehicles/{self.vehicle.id}/",
            {"model": "Tata Ace", "registered_number": "CG07XY0001",
                "status": "inactive"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- detail ---

    def test_detail_as_regular_user_returns_403(self):
        self.auth(self.regular)
        response = self.client.get(f"/api/v1/vehicles/{self.vehicle.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_detail_as_manager_returns_200(self):
        self.auth(self.manager)
        response = self.client.get(f"/api/v1/vehicles/{self.vehicle.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail_as_admin_returns_200(self):
        self.auth(self.admin)
        response = self.client.get(f"/api/v1/vehicles/{self.vehicle.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail_unauthenticated_returns_401(self):
        response = self.client.get(f"/api/v1/vehicles/{self.vehicle.id}/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- delete ---

    def test_delete_as_admin_returns_204(self):
        self.auth(self.admin)
        response = self.client.delete(f"/api/v1/vehicles/{self.vehicle.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Vehicle.objects.filter(id=self.vehicle.id).exists())

    def test_delete_as_manager_returns_403(self):
        """DELETE on a vehicle requires IsAdminUser; managers are forbidden."""
        self.auth(self.manager)
        response = self.client.delete(f"/api/v1/vehicles/{self.vehicle.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

class DriverAPITest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.admin = make_user("admin@d.com", "admin_d",
                               is_staff=True, is_superuser=True)
        self.manager = make_manager("manager@d.com", "manager_d")
        # Manager-with-profile: lets us also exercise the "manager sees own
        # /drivers/me" path later without polluting this class.
        self.manager_with_profile, _ = make_driver_user_with_profile(
            email="manager_dr@d.com", username="manager_dr",
            license_number="DL0000000001",
            phone_number="9100000090",
            name="Manager Driver",
        )
        self.manager_with_profile.is_manager = True
        self.manager_with_profile.save()
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
        response = self.client.get("/api/v1/drivers/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_as_regular_user_returns_403(self):
        """DriverListCreateView requires IsAdminUser | IsManager for ALL methods."""
        self.auth(self.regular)
        response = self.client.get("/api/v1/drivers/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_as_manager_returns_200(self):
        self.auth(self.manager)
        response = self.client.get("/api/v1/drivers/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_as_admin_returns_200(self):
        self.auth(self.admin)
        response = self.client.get("/api/v1/drivers/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # --- create ---

    def test_create_as_manager_returns_201(self):
        self.auth(self.manager)
        response = self.client.post(
            "/api/v1/drivers/", self._create_driver_payload(), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_also_creates_user_account(self):
        """DriverCreateSerializer.create() must create both a Driver and a User atomically."""
        self.auth(self.manager)
        payload = self._create_driver_payload(
            email="linked@d.com", username="linked_user",
            license="DL8888888888888", phone="9100008888"
        )
        self.client.post("/api/v1/drivers/", payload, format="json")
        self.assertTrue(User.objects.filter(email="linked@d.com").exists())

    def test_create_as_admin_returns_201(self):
        self.auth(self.admin)
        response = self.client.post(
            "/api/v1/drivers/",
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
            "/api/v1/drivers/", self._create_driver_payload(), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_with_duplicate_license_number_returns_400(self):
        self.auth(self.admin)
        payload = self._create_driver_payload(
            email="dup@d.com", username="dup_drv",
            license="DL1111111111111",   # duplicate
            phone="9100006666"
        )
        response = self.client.post("/api/v1/drivers/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- retrieve ---

    def test_retrieve_as_manager_returns_200(self):
        self.auth(self.manager)
        response = self.client.get(f"/api/v1/drivers/{self.driver.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_as_regular_user_returns_403(self):
        """DriverDetailView requires IsAdminUser | IsManager; regular users blocked."""
        self.auth(self.regular)
        response = self.client.get(f"/api/v1/drivers/{self.driver.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- update ---

    def test_update_as_manager_returns_200(self):
        self.auth(self.manager)
        response = self.client.patch(
            f"/api/v1/drivers/{self.driver.id}/",
            {"status": "inactive"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.driver.refresh_from_db()
        self.assertEqual(self.driver.status, "inactive")

    def test_update_as_regular_user_returns_403(self):
        self.auth(self.regular)
        response = self.client.patch(
            f"/api/v1/drivers/{self.driver.id}/",
            {"status": "inactive"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- delete ---

    def test_delete_as_admin_returns_403(self):
        """DriverDetailView.destroy() always raises PermissionDenied — even for admin.
        Deletion must happen via the User endpoint, not the Driver endpoint."""
        self.auth(self.admin)
        response = self.client.delete(f"/api/v1/drivers/{self.driver.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("You cannot delete driver", str(response.data))
        # The driver record must still exist.
        self.assertTrue(Driver.objects.filter(id=self.driver.id).exists())

    def test_delete_as_manager_returns_403(self):
        """Manager hit gets the same PermissionDenied override."""
        self.auth(self.manager)
        response = self.client.delete(f"/api/v1/drivers/{self.driver.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("You cannot delete driver", str(response.data))

    def test_destroy_returns_specific_error_message(self):
        """The PermissionDenied body must contain the exact override message."""
        self.auth(self.admin)
        response = self.client.delete(f"/api/v1/drivers/{self.driver.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("You cannot delete driver, delete the user.",
                      str(response.data))


# ---------------------------------------------------------------------------
# DriverMe  (self-service endpoint at /api/v1/drivers/me)
# ---------------------------------------------------------------------------

class DriverMeAPITest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        # Admin / manager available for cross-role assertions.
        self.admin = make_user("admin@me.com", "admin_me",
                               is_staff=True, is_superuser=True)
        self.manager = make_manager("manager@me.com", "manager_me")

        # Regular user WITH a driver profile (primary subject under test).
        self.driver_user, self.driver = make_driver_user_with_profile(
            email="driver@me.com", username="driver_me",
            license_number="DL2222222222222",
            phone_number="9300000001",
            name="Self Service Driver",
        )
        self.vehicle = make_vehicle("MEVEH001")
        self.driver.primary_vehicle = self.vehicle
        self.driver.save()

        # Regular user WITHOUT a driver profile.
        self.regular_no_profile = make_user(
            "noprofile@me.com", "noprofile_me"
        )

    def auth(self, user):
        self.client.force_authenticate(user=user)

    # --- GET ---

    def test_get_me_returns_driver_profile_for_authenticated_driver(self):
        """Authenticated driver sees their own profile at /drivers/me."""
        self.auth(self.driver_user)
        response = self.client.get("/api/v1/drivers/me")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Shape: id, name, phone_number, primary_vehicle (slug or null), user (uuid string).
        self.assertIn("id", response.data)
        self.assertIn("name", response.data)
        self.assertIn("phone_number", response.data)
        self.assertIn("primary_vehicle", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["name"], "Self Service Driver")
        self.assertEqual(response.data["phone_number"], "9300000001")
        self.assertEqual(
            response.data["primary_vehicle"], self.vehicle.registered_number)
        self.assertEqual(response.data["user"], self.driver_user.id)

    def test_get_me_unauthenticated_returns_401(self):
        response = self.client.get("/api/v1/drivers/me")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_me_returns_404_for_user_without_driver_profile(self):
        """DriverMeView.get_object raises NotFound when no Driver row exists."""
        self.auth(self.regular_no_profile)
        response = self.client.get("/api/v1/drivers/me")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_me_for_manager_with_driver_profile_returns_own_profile(self):
        """A manager who happens to have a Driver profile gets their OWN profile,
        not the list of drivers — because /drivers/me is scoped to request.user."""
        manager_with_profile, mgr_driver = make_driver_user_with_profile(
            email="mgr_driver@me.com", username="mgr_driver_me",
            license_number="DL2222222222223",
            phone_number="9300000002",
            name="Manager With Profile",
        )
        manager_with_profile.is_manager = True
        manager_with_profile.save()
        self.auth(manager_with_profile)
        response = self.client.get("/api/v1/drivers/me")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["license_number"], "DL2222222222223")
        self.assertEqual(response.data["name"], "Manager With Profile")

    def test_me_url_is_no_pk(self):
        """The endpoint must resolve without a UUID in the URL."""
        # The URL is literally /drivers/me — we just confirm GET works.
        # (If the URL accidentally required a UUID, this would 404.)
        self.auth(self.driver_user)
        response = self.client.get("/api/v1/drivers/me")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # --- PATCH ---

    def test_patch_me_allows_name_update(self):
        self.auth(self.driver_user)
        response = self.client.patch(
            "/api/v1/drivers/me",
            {"name": "Renamed Driver"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.driver.refresh_from_db()
        self.assertEqual(self.driver.name, "Renamed Driver")

    def test_patch_me_allows_phone_number_update(self):
        self.auth(self.driver_user)
        response = self.client.patch(
            "/api/v1/drivers/me",
            {"phone_number": "9300099999"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.driver.refresh_from_db()
        self.assertEqual(self.driver.phone_number, "9300099999")

    def test_patch_me_cannot_change_license_number(self):
        """license_number is read-only on DriverSelfSerializer; payload is ignored."""
        self.auth(self.driver_user)
        original_license = self.driver.license_number
        response = self.client.patch(
            "/api/v1/drivers/me",
            {"license_number": "DLXXXXXXXXXXXXX"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.driver.refresh_from_db()
        self.assertEqual(self.driver.license_number, original_license)

    def test_patch_me_cannot_change_status(self):
        """status is read-only on DriverSelfSerializer."""
        self.auth(self.driver_user)
        response = self.client.patch(
            "/api/v1/drivers/me",
            {"status": "inactive"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.driver.refresh_from_db()
        self.assertEqual(self.driver.status, "active")

    def test_patch_me_cannot_change_primary_vehicle(self):
        """primary_vehicle is read-only on DriverSelfSerializer."""
        self.auth(self.driver_user)
        other_vehicle = make_vehicle("OTHERME001")
        response = self.client.patch(
            "/api/v1/drivers/me",
            {"primary_vehicle": other_vehicle.registered_number},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.driver.refresh_from_db()
        self.assertEqual(self.driver.primary_vehicle, self.vehicle)

    def test_patch_me_unauthenticated_returns_401(self):
        response = self.client.patch(
            "/api/v1/drivers/me",
            {"name": "Hacker"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- DELETE ---

    def test_delete_me_returns_403_with_specific_message(self):
        """DriverMeView.destroy() always raises PermissionDenied with the
        self-delete override message — drivers must contact admin."""
        self.auth(self.driver_user)
        response = self.client.delete("/api/v1/drivers/me")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("You cannot delete your self!, contact admin.",
                      str(response.data))
        # Driver still exists.
        self.assertTrue(Driver.objects.filter(id=self.driver.id).exists())


# ---------------------------------------------------------------------------
# TripLog
# ---------------------------------------------------------------------------

class TripLogAPITest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.admin = make_user("admin@t.com", "admin_t",
                               is_staff=True, is_superuser=True)
        self.manager = make_manager("manager@t.com", "manager_t")
        self.regular = make_user("regular@t.com", "regular_t")

        self.vehicle = make_vehicle("TRIPVEH001")
        self.driver_user = make_user("driver@t.com", "driver_t")
        self.driver = make_driver(
            self.driver_user,
            license_number="DL2222222222222",
            phone_number="9200000001",
            name="Trip Driver",
            primary_vehicle=self.vehicle,
        )
        # Regular user WITHOUT a driver profile — exercises the NotFound paths.
        self.regular_no_profile = make_user(
            "noprofile@t.com", "noprofile_t"
        )
        self.trip = make_trip(self.vehicle, self.driver)

    def auth(self, user):
        self.client.force_authenticate(user=user)

    def _create_trip_payload(self, vehicle_number=None, **overrides):
        payload = {
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
        response = self.client.get("/api/v1/trip-logs/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_as_regular_user_only_sees_own_trips(self):
        """Seed two drivers' trips; the authed driver sees only their own."""
        # A second driver and a second trip.
        other_user = make_user("other@t.com", "other_t")
        other_driver = make_driver(
            other_user,
            license_number="DL3333333333333",
            phone_number="9200000002",
            primary_vehicle=self.vehicle,
        )
        make_trip(self.vehicle, other_driver)
        # Sanity: 2 trips exist in the DB.
        self.assertEqual(TripLog.objects.count(), 2)

        self.auth(self.driver_user)
        response = self.client.get("/api/v1/trip-logs/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        # Only the seeded self.trip is visible.
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["vehicle"]["registered_number"],
                         self.vehicle.registered_number)
        self.assertEqual(results[0]["driver"]["license_number"],
                         self.driver.license_number)

    def test_list_as_regular_user_without_driver_profile_returns_404(self):
        """get_queryset raises NotFound when the authed user has no profile."""
        self.auth(self.regular_no_profile)
        response = self.client.get("/api/v1/trip-logs/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_returns_200_and_nested_vehicle_for_authenticated_driver(self):
        """Driver-role user listing yields nested vehicle/driver objects."""
        self.auth(self.driver_user)
        response = self.client.get("/api/v1/trip-logs/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data["results"][0]
        self.assertIsInstance(result["vehicle"], dict)
        self.assertEqual(result["vehicle"]["registered_number"], "TRIPVEH001")

    def test_list_filter_by_vehicle_registered_number(self):
        other_vehicle = make_vehicle("FILTERVEH1")
        # Driver is scoped to their own trips; this other_vehicle is only on
        # the other driver's trips (still owned by self.driver in this fixture).
        # Use the driver-role user for the listing.
        self.auth(self.driver_user)
        # Create another trip on the filter vehicle, attached to self.driver.
        make_trip(other_vehicle, self.driver)
        response = self.client.get("/api/v1/trip-logs/?vehicle=FILTERVEH1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["vehicle"]["registered_number"], "FILTERVEH1"
        )

    def test_list_filter_by_date_range(self):
        make_trip(self.vehicle, self.driver, days_ago=5)   # outside range
        self.auth(self.driver_user)
        today = timezone.now().date().isoformat()
        response = self.client.get(
            f"/api/v1/trip-logs/?start_date={today}&end_date={today}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only today's trip should appear (the seeded one).
        self.assertEqual(len(response.data["results"]), 1)

    def test_list_filter_combined_vehicle_and_date_and_status(self):
        """Combined filters: vehicle + date range + is_approved status."""
        other_vehicle = make_vehicle("COMBOVEH1")
        # Trip 1: other_vehicle, 5 days ago, approved
        t1 = make_trip(other_vehicle, self.driver, days_ago=5)
        t1.is_approved = True
        t1.save()
        # Trip 2: other_vehicle, today, not approved
        make_trip(other_vehicle, self.driver, days_ago=0)
        # Trip 3: self.vehicle, today, approved
        t3 = make_trip(self.vehicle, self.driver, days_ago=0)
        t3.is_approved = True
        t3.save()

        self.auth(self.driver_user)
        today = timezone.now().date().isoformat()
        # Filter: other_vehicle + today + not approved
        response = self.client.get(
            f"/api/v1/trip-logs/?vehicle=COMBOVEH1&start_date={today}&end_date={today}&status=false")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["vehicle"]["registered_number"], "COMBOVEH1")
        self.assertFalse(response.data["results"][0]["is_approved"])

    def test_list_filter_by_driver_license_number(self):
        """Filter trip logs by driver license number (scoped to own trips)."""
        self.auth(self.driver_user)
        response = self.client.get(
            "/api/v1/trip-logs/?driver=DL2222222222222"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["driver"]["license_number"],
            "DL2222222222222"
        )

    # --- create ---
# problem here , 404 != 200.
    def test_create_as_driver_user_returns_201(self):
        self.auth(self.driver_user)
        response = self.client.post(
            "/api/v1/trip-logs/", self._create_trip_payload(), format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TripLog.objects.count(), 2)

    def test_create_unauthenticated_returns_401(self):
        response = self.client.post(
            "/api/v1/trip-logs/", self._create_trip_payload(), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_as_user_without_driver_profile_returns_404(self):
        """perform_create raises NotFound if the user has no driver_profile."""
        self.auth(self.regular_no_profile)
        response = self.client.post(
            "/api/v1/trip-logs/", self._create_trip_payload(), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_as_driver_auto_assigns_request_user_driver(self):
        """perform_create forces driver=request.user.driver_profile."""
        self.auth(self.driver_user)
        response = self.client.post(
            "/api/v1/trip-logs/", self._create_trip_payload(), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data["driver"]["license_number"],
            self.driver.license_number,
        )
        trip = TripLog.objects.get(id=response.data["id"])
        self.assertEqual(trip.driver, self.driver)

    def test_create_payload_driver_field_is_ignored(self):
        """Even if the payload includes a `driver` field, the server-assigned
        driver (request.user.driver_profile) wins. The serializer marks
        `driver` as read_only so DRF drops the incoming value."""
        other_user = make_user("other@t.com", "other_t")
        other_driver = make_driver(
            other_user,
            license_number="DL9999999999999",
            phone_number="9200000099",
            primary_vehicle=self.vehicle,
        )
        self.auth(self.driver_user)
        payload = self._create_trip_payload()
        payload["driver"] = other_driver.license_number   # sneaky injection
        response = self.client.post(
            "/api/v1/trip-logs/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        trip = TripLog.objects.get(id=response.data["id"])
        # Auto-assigned to the authenticated driver's profile, NOT the payload.
        self.assertEqual(trip.driver, self.driver)

    def test_create_without_weight_or_volume_returns_400(self):
        """Serializer validate() requires at least weight OR volume."""
        self.auth(self.driver_user)
        payload = {
            "date_time": timezone.now().isoformat(),
            "number_of_trips": 3,
            # no weight, no volume
        }
        response = self.client.post(
            "/api/v1/trip-logs/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_with_volume_only_returns_201(self):
        """Serializer accepts volume without weight (weight OR volume required)."""
        self.auth(self.driver_user)
        payload = {
            "date_time": timezone.now().isoformat(),
            "number_of_trips": 3,
            "volume": "5.00",
            # no weight
        }
        response = self.client.post(
            "/api/v1/trip-logs/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        trip = TripLog.objects.get(id=response.data["id"])
        self.assertEqual(trip.volume, Decimal("5.00"))
        self.assertIsNone(trip.weight)

    def test_create_without_vehicle_defaults_to_driver_primary_vehicle(self):
        """When no vehicle is sent, the serializer falls back to driver.primary_vehicle."""
        self.auth(self.driver_user)
        response = self.client.post(
            "/api/v1/trip-logs/", self._create_trip_payload(), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        trip_id = response.data["id"]
        trip = TripLog.objects.get(id=trip_id)
        self.assertEqual(trip.vehicle, self.driver.primary_vehicle)

    def test_create_with_explicit_vehicle_override_saves_that_vehicle(self):
        """Driver cannot change vehicle after creation. We assert the
        override is rejected on PATCH below; here we confirm creation
        still works when the driver explicitly names a different vehicle."""
        override_vehicle = make_vehicle("RIDE001")
        self.auth(self.driver_user)
        response = self.client.post(
            "/api/v1/trip-logs/",
            self._create_trip_payload(vehicle_number="RIDE001"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        trip = TripLog.objects.get(id=response.data["id"])
        self.assertEqual(trip.vehicle, override_vehicle)

    # --- detail ---

    def test_detail_returns_nested_driver_and_vehicle(self):
        self.auth(self.driver_user)
        response = self.client.get(f"/api/v1/trip-logs/{self.trip.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data["driver"], dict)
        self.assertIsInstance(response.data["vehicle"], dict)

    def test_detail_as_driver_for_own_trip_returns_200(self):
        self.auth(self.driver_user)
        response = self.client.get(f"/api/v1/trip-logs/{self.trip.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail_as_regular_user_for_other_drivers_trip_returns_404(self):
        """Regular-driver GET for someone else's trip is filtered out → 404."""
        other_user = make_user("other@t.com", "other_t")
        other_driver = make_driver(
            other_user,
            license_number="DL3333333333333",
            phone_number="9200000099",
            primary_vehicle=self.vehicle,
        )
        other_trip = make_trip(self.vehicle, other_driver)
        self.auth(self.driver_user)
        response = self.client.get(f"/api/v1/trip-logs/{other_trip.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- update ---

    def test_update_as_manager_with_reason_returns_200(self):
        self.auth(self.manager)
        response = self.client.patch(
            f"/api/v1/trip-logs/{self.trip.id}/",
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
            f"/api/v1/trip-logs/{self.trip.id}/",
            {"number_of_trips": 9},   # no reason provided
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_driver_can_update_own_trip_within_time_window(self):
        """
        A driver can edit a trip they just created, as long as it is within
        the allowed time window. The setUp trip is fresh, so we're inside.
        """
        self.auth(self.driver_user)
        response = self.client.patch(
            f"/api/v1/trip-logs/{self.trip.id}/",
            {
                "number_of_trips": 7,
                "last_reason_to_change": "Fixing count",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_driver_cannot_update_trip_outside_time_window(self):
        """
        We mock timezone.now() to return a time 3 hours AFTER the trip was
        created. This pushes the elapsed time past the 2-hour window and the
        serializer rejects with 400.

        WHY MOCK INSTEAD OF sleep():
          sleep(7200) would make this test take 2 hours.
          Mocking lets us simulate any point in time instantly.
        """
        self.auth(self.driver_user)
        future_time = timezone.now() + timedelta(hours=3)
        with patch("fleet.serializers_v1.triplog.timezone.now",
                   return_value=future_time):
            response = self.client.patch(
                f"/api/v1/trip-logs/{self.trip.id}/",
                {
                    "number_of_trips": 7,
                    "last_reason_to_change": "Too late",
                },
                format="json",
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_driver_can_update_trip_within_2_hours(self):
        """Driver CAN update a trip created 1 hour 59 minutes ago (within 2-hour window)."""
        self.auth(self.driver_user)
        future_time = timezone.now() + timedelta(hours=1, minutes=59)
        with patch("fleet.serializers_v1.triplog.timezone.now",
                   return_value=future_time):
            response = self.client.patch(
                f"/api/v1/trip-logs/{self.trip.id}/",
                {
                    "number_of_trips": 7,
                    "last_reason_to_change": "Within window",
                },
                format="json",
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_driver_cannot_update_trip_at_exactly_2_hours(self):
        """Driver CANNOT update a trip created exactly 2 hours ago (boundary is exclusive)."""
        self.auth(self.driver_user)
        future_time = timezone.now() + timedelta(hours=2)
        with patch("fleet.serializers_v1.triplog.timezone.now",
                   return_value=future_time):
            response = self.client.patch(
                f"/api/v1/trip-logs/{self.trip.id}/",
                {
                    "number_of_trips": 7,
                    "last_reason_to_change": "At boundary",
                },
                format="json",
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_driver_cannot_update_approved_trip(self):
        """Once a trip is approved (locked), even a timely edit by a driver must be rejected."""
        self.trip.is_approved = True
        self.trip.save()

        self.auth(self.driver_user)
        response = self.client.patch(
            f"/api/v1/trip-logs/{self.trip.id}/",
            {
                "number_of_trips": 7,
                "last_reason_to_change": "Should not work",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_driver_cannot_change_vehicle_after_creation(self):
        """The serializer rejects a vehicle change from the driver role."""
        other_vehicle = make_vehicle("OTHVEH001")
        self.auth(self.driver_user)
        response = self.client.patch(
            f"/api/v1/trip-logs/{self.trip.id}/",
            {
                "vehicle": other_vehicle.registered_number,
                "last_reason_to_change": "Swap truck",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- approve ---

    def test_approve_as_admin_returns_200_and_locks_trip(self):
        self.auth(self.admin)
        response = self.client.post(
            f"/api/v1/trip-logs/{self.trip.id}/approve/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.trip.refresh_from_db()
        self.assertTrue(self.trip.is_approved)

    def test_approve_as_manager_returns_200(self):
        self.auth(self.manager)
        response = self.client.post(
            f"/api/v1/trip-logs/{self.trip.id}/approve/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_approve_already_approved_trip_returns_400(self):
        """Approving twice should be rejected to prevent redundant DB writes."""
        self.auth(self.admin)
        # first approve
        self.client.post(f"/api/v1/trip-logs/{self.trip.id}/approve/")
        response = self.client.post(
            f"/api/v1/trip-logs/{self.trip.id}/approve/")   # second
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_approve_as_regular_user_returns_403(self):
        self.auth(self.regular)
        response = self.client.post(
            f"/api/v1/trip-logs/{self.trip.id}/approve/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_approve_nonexistent_trip_returns_404(self):
        self.auth(self.admin)
        import uuid
        fake_id = uuid.uuid4()
        response = self.client.post(f"/api/v1/trip-logs/{fake_id}/approve/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- delete ---

    def test_delete_as_admin_returns_204(self):
        self.auth(self.admin)
        response = self.client.delete(f"/api/v1/trip-logs/{self.trip.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TripLog.objects.filter(id=self.trip.id).exists())

    def test_delete_as_regular_user_returns_403(self):
        self.auth(self.regular)
        response = self.client.delete(f"/api/v1/trip-logs/{self.trip.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- single-trip calculation ---

    def test_calculate_weight_as_manager_returns_correct_amount(self):
        # amount = number_of_trips * weight * rate = 5 * 1000 * 10.50 = 52500
        self.auth(self.manager)
        response = self.client.post(
            f"/api/v1/trip-logs/{self.trip.id}/calculate/",
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
            f"/api/v1/trip-logs/{self.trip.id}/calculate/",
            {"rate": "2", "calc_type": "distance"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = float(Decimal("100.00") * 5 * Decimal("2"))
        self.assertAlmostEqual(response.data["amount"], expected, places=2)

    def test_calculate_volume_as_manager_returns_correct_amount(self):
        # Add volume to the existing trip
        self.trip.volume = Decimal("10.00")
        self.trip.save()
        # amount = 5 * 10 * 5 = 250
        self.auth(self.manager)
        response = self.client.post(
            f"/api/v1/trip-logs/{self.trip.id}/calculate/",
            {"rate": "5", "calc_type": "volume"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = float(Decimal("10.00") * 5 * Decimal("5"))
        self.assertAlmostEqual(response.data["amount"], expected, places=2)

    def test_calculate_with_invalid_calc_type_returns_400(self):
        self.auth(self.manager)
        response = self.client.post(
            f"/api/v1/trip-logs/{self.trip.id}/calculate/",
            {"rate": "10", "calc_type": "invalid_type"},   # invalid
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_calculate_with_missing_rate_returns_400(self):
        self.auth(self.manager)
        response = self.client.post(
            f"/api/v1/trip-logs/{self.trip.id}/calculate/",
            {"calc_type": "weight"},   # no rate
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_calculate_requires_manager_or_admin(self):
        self.auth(self.driver_user)
        response = self.client.post(
            f"/api/v1/trip-logs/{self.trip.id}/calculate/",
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
            "/api/v1/trip-logs/calculate-bulk/",
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
        # Other vehicle's trip is owned by another driver to avoid the
        # queryset filter hiding it. Then assert the vehicle filter
        # correctly excludes it.
        other_user = make_user("bv@t.com", "bv_t")
        other_driver = make_driver(
            other_user, license_number="DL5555555555555",
            phone_number="9200000099", primary_vehicle=other_vehicle
        )
        make_trip(other_vehicle, other_driver, weight="9999.00")

        self.auth(self.manager)
        today = timezone.now().date().isoformat()
        response = self.client.post(
            "/api/v1/trip-logs/calculate-bulk/",
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

    def test_bulk_calculate_volume_as_manager_returns_correct_total(self):
        """Test bulk calculation with volume calc_type."""
        make_trip(self.vehicle, self.driver,
                  number_of_trips=3, volume="20.00")
        self.auth(self.manager)
        today = timezone.now().date().isoformat()
        response = self.client.post(
            "/api/v1/trip-logs/calculate-bulk/",
            {
                "start_date": today,
                "end_date": today,
                "rate": "10",
                "calc_type": "volume",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_amount", response.data)
        self.assertIn("total_volume", response.data)
        self.assertGreater(response.data["total_amount"], 0)
        self.assertEqual(response.data["calc_type"], "volume")

    def test_bulk_calculate_distance_as_manager_returns_correct_total(self):
        """Test bulk calculation with distance calc_type."""
        make_trip(self.vehicle, self.driver,
                  number_of_trips=4, distance="50.00")
        self.auth(self.manager)
        today = timezone.now().date().isoformat()
        response = self.client.post(
            "/api/v1/trip-logs/calculate-bulk/",
            {
                "start_date": today,
                "end_date": today,
                "rate": "3",
                "calc_type": "distance",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_amount", response.data)
        self.assertIn("total_distance", response.data)
        self.assertGreater(response.data["total_amount"], 0)
        self.assertEqual(response.data["calc_type"], "distance")

    def test_bulk_calculate_invalid_calc_type_returns_400(self):
        """Test bulk calculation with invalid calc_type."""
        self.auth(self.manager)
        today = timezone.now().date().isoformat()
        response = self.client.post(
            "/api/v1/trip-logs/calculate-bulk/",
            {
                "start_date": today,
                "end_date": today,
                "rate": "5",
                "calc_type": "invalid_calc_type",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_bulk_calculate_rate_too_small_returns_400(self):
        """Test bulk calculation with rate < 1."""
        self.auth(self.manager)
        today = timezone.now().date().isoformat()
        response = self.client.post(
            "/api/v1/trip-logs/calculate-bulk/",
            {
                "start_date": today,
                "end_date": today,
                "rate": "0.5",
                "calc_type": "weight",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_bulk_calculate_with_invalid_date_format_returns_400(self):
        self.auth(self.manager)
        response = self.client.post(
            "/api/v1/trip-logs/calculate-bulk/",
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
            "/api/v1/trip-logs/calculate-bulk/",
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
            "/api/v1/trip-logs/calculate-bulk/",
            {"start_date": today, "end_date": today,
             "rate": "5", "calc_type": "weight"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_bulk_calculate_with_nonexistent_vehicle_returns_404(self):
        self.auth(self.manager)
        today = timezone.now().date().isoformat()
        response = self.client.post(
            "/api/v1/trip-logs/calculate-bulk/",
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

    def test_bulk_calculate_volume_with_nonexistent_vehicle_returns_404(self):
        self.auth(self.manager)
        today = timezone.now().date().isoformat()
        response = self.client.post(
            "/api/v1/trip-logs/calculate-bulk/",
            {
                "start_date": today,
                "end_date": today,
                "rate": "5",
                "calc_type": "volume",
                "vehicle": "GHOST999",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_bulk_calculate_distance_with_nonexistent_vehicle_returns_404(self):
        self.auth(self.manager)
        today = timezone.now().date().isoformat()
        response = self.client.post(
            "/api/v1/trip-logs/calculate-bulk/",
            {
                "start_date": today,
                "end_date": today,
                "rate": "5",
                "calc_type": "distance",
                "vehicle": "GHOST999",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# User (via /api/v1/users/<uuid:pk>/) and /api/v1/users/ list
# ---------------------------------------------------------------------------

class UserAPITest(APITestCase):
    """
    Tests for UserDetailView (RetrieveDestroyAPIView — no PATCH/PUT anymore)
    and UserListView.

    NOTE: PATCH was removed in commit 05a1b24 — UserDetailView is now
    RetrieveDestroyAPIView, so PATCH/PUT return 405 Method Not Allowed.
    User creation happens via the nested payload in DriverCreateSerializer.
    """

    def setUp(self):
        self.client = APIClient()
        self.admin = make_user("admin@u.com", "admin_u",
                               is_staff=True, is_superuser=True)
        self.manager = make_manager("manager@u.com", "manager_u")
        self.regular = make_user("regular@u.com", "regular_u")

    def auth(self, user):
        self.client.force_authenticate(user=user)

    # --- /api/v1/users/<uuid>/  retrieve ---

    def test_admin_can_retrieve_any_user(self):
        self.auth(self.admin)
        response = self.client.get(f"/api/v1/users/{self.regular.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.regular.email)

    def test_manager_can_retrieve_any_user(self):
        self.auth(self.manager)
        response = self.client.get(f"/api/v1/users/{self.regular.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_retrieve_other_users_returns_404(self):
        self.auth(self.regular)
        response = self.client.get(f"/api/v1/users/{self.admin.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_regular_user_can_retrieve_own_profile(self):
        """Self-lookup is allowed by the UserDetailView queryset filter."""
        self.auth(self.regular)
        response = self.client.get(f"/api/v1/users/{self.regular.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.regular.email)

    def test_unauthenticated_cannot_retrieve_user(self):
        response = self.client.get(f"/api/v1/users/{self.regular.id}/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- /api/v1/users/<uuid>/  update (no longer supported) ---

    def test_admin_can_update_user(self):
        """UserDetailView is now RetrieveDestroyAPIView → PATCH returns 405."""
        self.auth(self.admin)
        response = self.client.patch(
            f"/api/v1/users/{self.regular.id}/",
            {"username": "updated_name"},
            format="json",
        )
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_manager_cannot_update_user_via_patch(self):
        """Manager is blocked at the IsAdminUser permission check before reaching the method gate."""
        self.auth(self.manager)
        response = self.client.patch(
            f"/api/v1/users/{self.regular.id}/",
            {"username": "manager_updated"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    #  this test need 403 not 405 as its caused by PBAC not because patch/put methods dont exist for this url.
    def test_regular_user_cannot_update_users(self):
        """PATCH blocked at the permission layer (403) for non-admin roles."""
        self.auth(self.regular)
        response = self.client.patch(
            f"/api/v1/users/{self.regular.id}/",
            {"username": "self_update"},
            format="json",
        )
        self.assertEqual(response.status_code,
                         status.HTTP_403_FORBIDDEN)

    # --- /api/v1/users/<uuid>/  delete ---

    def test_admin_can_delete_user(self):
        target = make_user("delete_me@u.com", "delete_me_u")
        self.auth(self.admin)
        response = self.client.delete(f"/api/v1/users/{target.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=target.id).exists())

    def test_manager_cannot_delete_user(self):
        """DELETE requires IsAdminUser; managers are blocked at the permission layer."""
        target = make_user("delete_by_manager@u.com", "delete_manager_u")
        self.auth(self.manager)
        response = self.client.delete(f"/api/v1/users/{target.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(User.objects.filter(id=target.id).exists())

    def test_regular_user_cannot_delete_users(self):
        target = make_user("no_delete@u.com", "no_delete_u")
        self.auth(self.regular)
        response = self.client.delete(f"/api/v1/users/{target.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_delete_user(self):
        target = make_user("no_auth_delete@u.com", "no_auth_delete_u")
        response = self.client.delete(f"/api/v1/users/{target.id}/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- /api/v1/users/  list endpoint ---

    def test_users_list_endpoint_requires_admin_or_manager(self):
        # admin → 200
        self.auth(self.admin)
        response = self.client.get("/api/v1/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # manager → 200
        self.auth(self.manager)
        response = self.client.get("/api/v1/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # regular → 403
        self.auth(self.regular)
        response = self.client.get("/api/v1/users/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # unauthenticated → 401 (clear the forced auth first)
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/v1/users/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_users_list_as_regular_user_returns_403(self):
        self.auth(self.regular)
        response = self.client.get("/api/v1/users/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_users_list_as_manager_returns_200(self):
        """Manager gets a paginated list back."""
        self.auth(self.manager)
        response = self.client.get("/api/v1/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # UserListView is ListAPIView → paginated response has 'results'.
        self.assertIn("results", response.data)
        self.assertGreaterEqual(len(response.data["results"]), 1)


# ---------------------------------------------------------------------------
# Change password (/api/v1/users/me/change-password/)
# ---------------------------------------------------------------------------

class UserChangePasswordAPITest(APITestCase):
    """
    Tests for ChangePasswordView. The URL has no <pk> segment; get_object()
    returns request.user, so only the authed user's password can be changed.
    """

    URL = "/api/v1/users/me/change-password/"
    NEW_PASSWORD = "NewStrong456!"

    def setUp(self):
        self.client = APIClient()
        # User whose password we will mutate. Known old password.
        self.regular = make_user("pw@u.com", "pwuser", "OldPass123")
        # A second user — to confirm the change-password call does NOT touch
        # other users.
        self.other_user = make_user("other@u.com", "other_u", "OtherPass123")

    def auth(self, user):
        self.client.force_authenticate(user=user)

    # --- happy path ---

    def test_change_password_authenticated_returns_200(self):
        self.auth(self.regular)
        response = self.client.patch(
            self.URL,
            {"password": self.NEW_PASSWORD, "password_confirm": self.NEW_PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_password_updates_password_in_db(self):
        """After the call, user.check_password(NEW_PASSWORD) must be True."""
        self.auth(self.regular)
        self.client.patch(
            self.URL,
            {"password": self.NEW_PASSWORD, "password_confirm": self.NEW_PASSWORD},
            format="json",
        )
        self.regular.refresh_from_db()
        self.assertTrue(self.regular.check_password(self.NEW_PASSWORD))
        # Old password is gone.
        self.assertFalse(self.regular.check_password("OldPass123"))

    def test_change_password_targets_request_user_not_url_pk(self):
        """The URL has no <pk>; get_object() returns request.user. We assert
        this conceptually by checking that the request user's password is the
        one that changed."""
        self.auth(self.regular)
        self.client.patch(
            self.URL,
            {"password": self.NEW_PASSWORD, "password_confirm": self.NEW_PASSWORD},
            format="json",
        )
        self.regular.refresh_from_db()
        self.assertTrue(self.regular.check_password(self.NEW_PASSWORD))

    def test_change_password_does_not_affect_other_users_password(self):
        """Other users in the DB keep their passwords."""
        self.auth(self.regular)
        self.client.patch(
            self.URL,
            {"password": self.NEW_PASSWORD, "password_confirm": self.NEW_PASSWORD},
            format="json",
        )
        self.other_user.refresh_from_db()
        self.assertTrue(self.other_user.check_password("OtherPass123"))

    # --- validation failures ---

    def test_change_password_with_mismatched_confirm_returns_400(self):
        self.auth(self.regular)
        response = self.client.patch(
            self.URL,
            {"password": self.NEW_PASSWORD, "password_confirm": "DifferentValue"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_without_password_field_returns_400(self):
        self.auth(self.regular)
        response = self.client.patch(
            self.URL,
            {"password_confirm": self.NEW_PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_without_confirm_returns_400(self):
        self.auth(self.regular)
        response = self.client.patch(
            self.URL,
            {"password": self.NEW_PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_with_weak_password_returns_400(self):
        """Django's validate_password rejects trivial passwords like '123'."""
        self.auth(self.regular)
        response = self.client.patch(
            self.URL,
            {"password": "123", "password_confirm": "123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- auth ---

    def test_change_password_unauthenticated_returns_401(self):
        response = self.client.patch(
            self.URL,
            {"password": self.NEW_PASSWORD, "password_confirm": self.NEW_PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Health check (/health/)  — config.views.HealthCheckView
# ---------------------------------------------------------------------------

class TestHealth(APITestCase):
    """
    Unit / integration tests for the unversioned /health/ endpoint.
    The endpoint is used by container orchestrators (k8s, docker, etc.),
    so it must be AllowAny, return 200, and reflect DB connectivity.
    """

    URL = "/health/"

    def setUp(self):
        self.client = APIClient()

    def test_health_returns_200(self):
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health_reports_database_connected_when_db_reachable(self):
        """Default test DB is reachable — database must be 'connected'."""
        response = self.client.get(self.URL)
        self.assertEqual(response.data["database"], "connected")

    def test_health_reports_database_disconnected_when_ensure_connection_raises(self):
        """When ensure_connection() raises, the view must report 'disconnected'."""
        with patch("config.views.connection.ensure_connection",
                   side_effect=Exception("db down")):
            response = self.client.get(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["database"], "disconnected")

    def test_health_does_not_require_authentication(self):
        """No force_authenticate, no cookie — must still be 200."""
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health_response_payload_shape(self):
        """Payload must include 'status' and 'database' keys."""
        response = self.client.get(self.URL)
        self.assertIn("status", response.data)
        self.assertIn("database", response.data)
        self.assertEqual(response.data["status"], "healthy")


# ---------------------------------------------------------------------------
# TripLogService unit tests  — services_v1/triplog_service/triplog_service.py
#
# These tests bypass HTTP and call the service layer directly. They cover the
# error branches in calculate_single and calculate_bulk that the API tests do
# not (the views layer surfaces them as 4xx, but here we assert the exact
# exception class and message).
# ---------------------------------------------------------------------------

class TestTripLogService(APITestCase):
    """Direct unit tests for TripLogService — no HTTP, no DRF."""

    def setUp(self):
        self.user = make_user("svc@trip.com", "svcuser")
        self.vehicle = make_vehicle("SVCVEH001")
        self.driver = make_driver(
            self.user,
            license_number="DL4444444444444",
            phone_number="9400000001",
            primary_vehicle=self.vehicle,
        )
        self.trip = make_trip(
            self.vehicle, self.driver,
            number_of_trips=4, weight="800.00", distance="200.00",
        )

    # --- calculate_single: error branches ---

    def test_calculate_single_raises_trip_not_found(self):
        from services_v1.triplog_service.triplog_service import TripLogService
        from services_v1.triplog_service.exceptions import TripNotFound
        import uuid
        with self.assertRaises(TripNotFound):
            TripLogService.calculate_single(
                uuid.uuid4(), Decimal("10"), "weight")

    def test_calculate_single_raises_for_invalid_calc_type(self):
        from services_v1.triplog_service.triplog_service import TripLogService
        from services_v1.triplog_service.exceptions import InvalidCalculationInput
        with self.assertRaises(InvalidCalculationInput):
            TripLogService.calculate_single(
                self.trip.id, Decimal("10"), "not_a_real_type")

    def test_calculate_single_raises_when_rate_less_than_one(self):
        from services_v1.triplog_service.triplog_service import TripLogService
        from services_v1.triplog_service.exceptions import InvalidCalculationInput
        with self.assertRaises(InvalidCalculationInput):
            TripLogService.calculate_single(
                self.trip.id, Decimal("0.5"), "weight")

    def test_calculate_single_weight_raises_when_weight_is_null(self):
        from services_v1.triplog_service.triplog_service import TripLogService
        from services_v1.triplog_service.exceptions import InvalidCalculationInput
        self.trip.weight = None
        self.trip.save()
        with self.assertRaises(InvalidCalculationInput):
            TripLogService.calculate_single(
                self.trip.id, Decimal("10"), "weight")

    def test_calculate_single_volume_raises_when_volume_is_null(self):
        from services_v1.triplog_service.triplog_service import TripLogService
        from services_v1.triplog_service.exceptions import InvalidCalculationInput
        self.trip.volume = None
        self.trip.save()
        with self.assertRaises(InvalidCalculationInput):
            TripLogService.calculate_single(
                self.trip.id, Decimal("10"), "volume")

    def test_calculate_single_distance_raises_when_distance_is_null(self):
        from services_v1.triplog_service.triplog_service import TripLogService
        from services_v1.triplog_service.exceptions import InvalidCalculationInput
        self.trip.distance_traveled = None
        self.trip.save()
        with self.assertRaises(InvalidCalculationInput):
            TripLogService.calculate_single(
                self.trip.id, Decimal("10"), "distance")

    # --- calculate_single: happy paths ---

    def test_calculate_single_weight_happy_path(self):
        from services_v1.triplog_service.triplog_service import TripLogService
        result = TripLogService.calculate_single(
            self.trip.id, Decimal("5"), "weight")
        # amount = 4 trips * 800 * 5 = 16000
        self.assertEqual(result["amount"], 16000.0)
        self.assertEqual(result["calc_type"], "weight")
        self.assertEqual(result["quantity_per_trip"], 800.0)
        self.assertEqual(result["total_quantity"], 3200.0)

    def test_calculate_single_volume_happy_path(self):
        from services_v1.triplog_service.triplog_service import TripLogService
        self.trip.volume = Decimal("20.00")
        self.trip.save()
        result = TripLogService.calculate_single(
            self.trip.id, Decimal("3"), "volume")
        # amount = 4 * 20 * 3 = 240
        self.assertEqual(result["amount"], 240.0)

    def test_calculate_single_distance_happy_path(self):
        from services_v1.triplog_service.triplog_service import TripLogService
        result = TripLogService.calculate_single(
            self.trip.id, Decimal("2.5"), "distance")
        # amount = 4 * 200 * 2.5 = 2000
        self.assertEqual(result["amount"], 2000.0)

    # --- calculate_bulk: error branches ---

    def test_calculate_bulk_raises_when_rate_less_than_one(self):
        from services_v1.triplog_service.triplog_service import TripLogService
        from services_v1.triplog_service.exceptions import InvalidCalculationInput
        today = timezone.now().date().isoformat()
        with self.assertRaises(InvalidCalculationInput):
            TripLogService.calculate_bulk(
                today, today, Decimal("0.1"), "weight")

    def test_calculate_bulk_raises_for_invalid_calc_type(self):
        from services_v1.triplog_service.triplog_service import TripLogService
        from services_v1.triplog_service.exceptions import InvalidCalculationInput
        today = timezone.now().date().isoformat()
        with self.assertRaises(InvalidCalculationInput):
            TripLogService.calculate_bulk(
                today, today, Decimal("5"), "garbage_type")

    # --- approve_trip: edge cases ---

    def test_approve_trip_raises_trip_not_found(self):
        from services_v1.triplog_service.triplog_service import TripLogService
        from services_v1.triplog_service.exceptions import TripNotFound
        import uuid
        with self.assertRaises(TripNotFound):
            TripLogService.approve_trip(uuid.uuid4())
