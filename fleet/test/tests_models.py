from django.test import TestCase
from fleet.models import Vehicle, Driver, TripLog
from decimal import Decimal
from django.utils import timezone


# Create your tests here.
class VehicleModelTest(TestCase):
    """test vehicle models"""

    def setUp(self):
        """run before each test - create test data"""
        self.vehicle = Vehicle.objects.create(
            registered_number="TEST1234",
            model="Tata Ace",
            status="active"
        )

    def test_vehicle_creation(self):
        """test vehicle is created correctly"""
        self.assertEqual(self.vehicle.registered_number, "TEST1234")
        self.assertEqual(self.vehicle.model, "Tata Ace")
        self.assertEqual(self.vehicle.status, "active")

    def test_vehicle_str(self):
        """test vehicel string representation"""
        expected = "Vehicle: TEST1234"
        self.assertEqual(str(self.vehicle), expected)

    def test_unique_registered_number(self):
        """test registered_number must be unique"""
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            Vehicle.objects.create(
                registered_number="TEST1234",
                model="Different Model",
                status="active"
            )

    def test_default_ordering(self):
        """test vehicles are ordered by status, then registered_number"""
        Vehicle.objects.create(
            registered_number="AAA",
            status="inactive"
        )
        Vehicle.objects.create(
            registered_number="ZZZ",
            status="active"
        )

        vehicles = list(Vehicle.objects.all())
        self.assertEqual(vehicles[0].status, "inactive")
        self.assertEqual(vehicles[1].status, "active")
        self.assertEqual(vehicles[2].status, "active")

        self.assertEqual(vehicles[0].registered_number, "AAA")
        self.assertEqual(vehicles[1].registered_number, "TEST1234")
        self.assertEqual(vehicles[2].registered_number, "ZZZ")


class DriverModelTest(TestCase):
    """test class to test driver models """

    def setUp(self):
        self.driver = Driver.objects.create(
            name="ABC1",
            license_number="123456789123456",
            status="active"
        )

    def test_driver_creation(self):
        """test if the driver is created correctly"""
        self.assertEqual(self.driver.name, "ABC1")
        self.assertEqual(self.driver.license_number, "123456789123456")
        self.assertEqual(self.driver.status, "active")

    def test_driver_str(self):
        """test the string representation of driver model"""
        expected = "Driver: ABC1 (123456789123456)"
        self.assertEqual(str(self.driver), expected)

    def test_unique_license_number(self):
        """test driver  license number validity and lenghth"""
        self.assertEqual(len(self.driver.license_number), 15)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Driver.objects.create(
                name="ABC2",
                license_number="123456789123456",
                status="active"
            )

    def test_driver_ordering(self):
        """test ordering of driver , by status first then name"""
        Driver.objects.create(
            name="BCD",
            license_number="123456789123457",
            status="active"
        )
        Driver.objects.create(
            name="CDE",
            license_number="123456789123458",
            status="active"
        )

        drivers = list(Driver.objects.all())
        self.assertEqual(drivers[0].license_number, "123456789123456")
        self.assertEqual(drivers[1].license_number, "123456789123457")
        self.assertEqual(drivers[2].license_number, "123456789123458")

        self.assertEqual(drivers[0].name, "ABC1")
        self.assertEqual(drivers[1].name, "BCD")
        self.assertEqual(drivers[2].name, "CDE")


class TripLogModelTest(TestCase):
    def setUp(self):
        self.vehicle = Vehicle.objects.create(
            registered_number="TRUCK001",
            status="active"
        )
        self.driver = Driver.objects.create(
            name="Test Driver",
            license_number="DL999",
            status="active"
        )
        self.trip = TripLog.objects.create(
            vehicle=self.vehicle,
            driver=self.driver,
            date_time=timezone.now(),
            number_of_trips=5,
            weight=Decimal("1000.50"),
            distance_traveled=Decimal("150.75")
        )

    def test_trip_creation(self):
        """Test trip log is created correctly"""
        self.assertEqual(self.trip.vehicle, self.vehicle)
        self.assertEqual(self.trip.driver, self.driver)
        self.assertEqual(self.trip.number_of_trips, 5)

    def test_nullable_fields(self):
        """Test weight and distance can be null"""
        trip = TripLog.objects.create(
            vehicle=self.vehicle,
            driver=self.driver,
            date_time=timezone.now(),
            number_of_trips=3
            # weight and distance not provided
        )
        self.assertIsNone(trip.weight)
        self.assertIsNone(trip.distance_traveled)
