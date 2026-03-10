from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from fleet.models import *
from decimal import Decimal
from django.utils import timezone
import json


class VehicleAPITest(APITestCase):
    """test vehicle API endpoints"""

    def setUp(self):
        """setup for testing vehicle api endpoint  and creating user"""

        self.client = APIClient()

        # creating test admin user
        self.admin_user = User.objects.create_superuser(
            username="admin",
            password="admin123",
            email="admin@test.com"

        )

        # create test regular user
        self.regular_user = User.objects.create(
            username="TestUser",
            password="testPassword",
            email="testuser@test.com"
        )

        # creating a default test vehicle
        self.vehicle = Vehicle.objects.create(
            model="Tata Ace",
            registered_number="CG07XY1234",
            status="active"
        )

    def test_vehicle_creation_as_admin(self):
        """test a new vehicle is created with valid data and created correctly"""
        payload = {
            "model": "Tata Ace",
            "registered_number": "CG07XY1235",
            "status": "active"
        }

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post("/api/vehicles/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Vehicle.objects.count(), 2)

    def test_vehicle_creation_as_regular_user(self):
        """test vehicle creation as regular user which should fail"""
        payload = {
            "model": "Tata Ace",
            "registered_number": "CG07XY1235",
            "status": "active"
        }
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post("/api/vehicles/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_vehicle_listing_unauthenticated(self):
        """test list of vehicle is displayed or returned correctly """
        response = self.client.get("/api/vehicles/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_list_vehicle_with_pagination(self):
        """test pagination at work"""
        # generate random data to fill up vehicle list
        for i in range(11):
            Vehicle.objects.create(
                model=f"Tata Ace{str(i)}",
                registered_number=f"CG07XY{str(i)}23",
                status='active'
            )
        response = self.client.get("/api/vehicles/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)

    def test_list_vehicle_filtering(self):
        """test vehcie listing with filteration"""
        payload = {
            "model": "tata",
            "registered_number": "CG07CY1234",
            "status": "inactive"
        }
        self.client.force_authenticate(user=self.admin_user)
        self.client.post("/api/vehicles/", payload)
        response = self.client.get("/api/vehicles/")

    def test_update_vehicle_as_admin(self):
        """admin can update vehicle"""
        self.client.force_authenticate(user=self.admin_user)

        data = {"status": "inactive"}
        response = self.client.patch(f"/api/vehicles/{self.vehicle.id}/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.status, "inactive")


class TripLogAPITest(APITestCase):
    """Test TripLog API endpoints"""

    def setUp(self):
        """Setup test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='test123'
        )

        self.vehicle = Vehicle.objects.create(
            registered_number="TRUCK001",
            status="active"
        )

        self.driver = Driver.objects.create(
            name="Test Driver",
            license_number="DL12345",
            status="active"
        )

        self.trip = TripLog.objects.create(
            vehicle=self.vehicle,
            driver=self.driver,
            date_time=timezone.now(),
            number_of_trips=5,
            weight=Decimal("1000.00"),
            distance_traveled=Decimal("100.00")
        )

        self.client = APIClient()

    def test_list_trips_authenticated(self):
        """Authenticated users can view trips"""
        self.client.force_authenticate(user=self.user)

        response = self.client.get('/api/trip-logs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_trips_unauthenticated(self):
        """Unauthenticated users cannot view trips"""
        response = self.client.get('/api/trip-logs/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_calculate_single_trip_weight(self):
        """Test single trip calculation by weight"""
        self.client.force_authenticate(user=self.user)

        data = {
            'rate': '10.50',
            'calc_type': 'weight'
        }

        response = self.client.post(
            f'/api/trip-logs/{self.trip.id}/calculate/',
            data
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('amount', response.data)

        # Expected: 5 trips * 1000 kg * 10.50 = 52,500
        expected = float(5 * 1000 * Decimal('10.50'))
        self.assertEqual(float(response.data['amount']), expected)
