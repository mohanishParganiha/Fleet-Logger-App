from time import sleep
from fleet.models import Vehicle, Driver, TripLog
from datetime import timedelta
from django.utils import timezone
from decimal import Decimal
from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from django.contrib.auth import get_user_model
from django.test import override_settings


@override_settings(
    SESSION_COOKIE_DOMAIN='api.testserver',
    CSRF_COOKIE_DOMAIN='api.testserver'
)
class AuthenticationTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()

        User = get_user_model()

        self.user = User.objects.create_user(
            email='test@email.com',
            username='Test User',
            password='TestPass123'
        )

    def test_login_authenticate_sucess(self):
        """Test if login is sucessful."""
        response = self.client.post(
            '/api/login/',
            {
                'email': 'test@email.com',
                'password': 'TestPass123'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('auth_token', response.cookies)
        self.assertTrue(response.cookies['auth_token']['httponly'])

    def test_endpoint_injecting_token_in_cookies(self):
        """Test  endpoint response ok by injecting token in cookies."""
        token = Token.objects.create(user=self.user)

        self.client.cookies['auth_token'] = token.key
        self.client.cookies['auth_token']['domain'] = 'api.testserver'

        response = self.client.get('/api/drivers/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_clears_cookies(self):
        """Test user logout clears cookies."""
        token = Token.objects.create(user=self.user)

        self.client.cookies['auth_token'] = token.key
        self.client.cookies['auth_token']['domain'] = 'api.testserver'

        response = self.client.post(
            '/api/logout/'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('auth_token', response.cookies)

        logout_cookie = response.cookies['auth_token']
        # Standard format used by Django test client
        self.assertEqual(logout_cookie['max-age'], 0)
        # Value should be completely wiped blank
        self.assertEqual(logout_cookie.value, '')

        # Assertion 4: Verify the token was permanently erased from the database
        token_exists = Token.objects.filter(key=token.key).exists()
        self.assertFalse(token_exists)


class VehicleAPITest(APITestCase):
    """Test Vhicle Endpoints."""

    def setUp(self):
        User = get_user_model()

        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            email='admin@test.com',
            username='admin',
            password='admin123'
        )
        self.manager_user = User.objects.create_user(
            email='manager@test.com',
            username='manager',
            password='manager123',
            is_manager=True
        )
        self.regular_user = User.objects.create_user(
            email='user@test.com',
            username='user',
            password='user123'
        )
        self.vehicle = Vehicle.objects.create(
            model='Tata Ace',
            registered_number='CG07XY1234',
            status='active'
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_vehicle_list_requires_authentication(self):
        """Test vhicle listing requires authentication."""
        response = self.client.get('/api/vehicles/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_vehicle_list_authenticated_returns_results(self):
        """Test vehicle authenticated vehicle listing returns response."""
        self.authenticate(self.regular_user)
        response = self.client.get('/api/vehicles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results']
                         [0]['registered_number'], 'CG07XY1234')

    def test_vehicle_list_pagination_works(self):
        """Test pagination of vehicle listing."""
        self.authenticate(self.regular_user)
        for index in range(11):
            Vehicle.objects.create(
                model=f'Tata Ace {index}',
                registered_number=f'CG07XY12{index:02d}',
                status='active'
            )
        response = self.client.get('/api/vehicles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)

    def test_vehicle_filtering_by_status(self):
        """Test filtering vehicle listing by status """
        self.authenticate(self.regular_user)
        Vehicle.objects.create(
            model='Tata Ace',
            registered_number='CG07XY9999',
            status='inactive'
        )
        response = self.client.get('/api/vehicles/?status=inactive')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['status'], 'inactive')

    def test_vehicle_create_as_admin(self):
        """Test vehicle created as admin."""
        self.authenticate(self.admin_user)
        response = self.client.post(
            '/api/vehicles/',
            {'model': 'Tata Ace', 'registered_number': 'CG07XY1235', 'status': 'active'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Vehicle.objects.filter(
            registered_number='CG07XY1235').count(), 1)

    def test_vehicle_create_as_manager(self):
        """Test vehicle create as manager."""
        self.authenticate(self.manager_user)
        response = self.client.post(
            '/api/vehicles/',
            {'model': 'Tata Ace', 'registered_number': 'CG07XY1236', 'status': 'active'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_vehicle_create_as_regular_user_is_forbidden(self):
        """Test vehicle create as regular user is forbidden."""
        self.authenticate(self.regular_user)
        response = self.client.post(
            '/api/vehicles/',
            {'model': 'Tata Ace', 'registered_number': 'CG07XY1237', 'status': 'active'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_vehicle_create_unauthenticated_is_unauthorized(self):
        """Test vehicle create as unauthenticated is forbidden. """
        response = self.client.post(
            '/api/vehicles/',
            {'model': 'Tata Ace', 'registered_number': 'CG07XY1237', 'status': 'active'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_vehicle_detail_requires_authentication(self):
        """Test vehicle detail requires authentication."""
        response = self.client.get(f'/api/vehicles/{self.vehicle.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_vehicle_update_as_manager(self):
        """Test vehicle update as manager."""
        self.authenticate(self.manager_user)
        response = self.client.patch(
            f'/api/vehicles/{self.vehicle.id}/',
            {'status': 'inactive'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.status, 'inactive')

    def test_vehicle_update_as_regular_user_forbidden(self):
        """Test vehicle update as regular user is forbidden."""
        self.authenticate(self.regular_user)
        response = self.client.patch(
            f'/api/vehicles/{self.vehicle.id}/',
            {'status': 'inactive'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_vehicle_delete_as_admin(self):
        """Test vehicle delete as admin."""
        self.authenticate(self.admin_user)
        response = self.client.delete(f'/api/vehicles/{self.vehicle.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Vehicle.objects.filter(id=self.vehicle.id).exists())

    def test_vehicle_delete_as_manager_forbidden(self):
        """Test vehicle delete as manager is forbidden."""
        self.authenticate(self.manager_user)
        response = self.client.delete(f'/api/vehicles/{self.vehicle.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class DriverAPITest(APITestCase):
    """Test for Driver API."""

    def setUp(self):
        User = get_user_model()

        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            email='admin@test.com',
            username='admin',
            password='admin123'
        )
        self.manager_user = User.objects.create_user(
            email='manager@test.com',
            username='manager',
            password='manager123',
            is_manager=True
        )
        self.regular_user = User.objects.create_user(
            email='user@test.com',
            username='user',
            password='user123'
        )
        self.driver = Driver.objects.create(
            name='Test Driver',
            license_number='DL12345',
            status='active'
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_driver_list_requires_authentication(self):
        """Test driver listing requires authentication."""
        response = self.client.get('/api/drivers/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_driver_list_authenticated(self):
        """Test driver listing as authenticated."""
        self.authenticate(self.regular_user)
        response = self.client.get('/api/drivers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results']
                         [0]['license_number'], 'DL12345')

    def test_driver_create_as_manager(self):
        """Test driver creation as manager."""
        self.authenticate(self.manager_user)
        response = self.client.post(
            '/api/drivers/',
            {'name': 'New Driver', 'license_number': 'DL99999', 'status': 'active'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_driver_create_as_regular_user_forbidden(self):
        """Test driver creation as regular user is forbidden."""
        self.authenticate(self.regular_user)
        response = self.client.post(
            '/api/drivers/',
            {'name': 'New Driver', 'license_number': 'DL99999', 'status': 'active'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_driver_create_as_manager_linking_user(self):
        """Test the creation of driver with linked user"""
        self.authenticate(self.manager_user)
        response = self.client.post(
            '/api/drivers/',
            {'name': 'New Driver 2', 'license_number': 'DL999991',
                'status': 'active', 'user': self.regular_user.id},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_driver_create_as_admin_linking_user(self):
        """Test the creation of driver with linked user"""
        self.authenticate(self.admin_user)

        response = self.client.post(
            '/api/drivers/',
            {'name': 'New Driver 3', 'license_number': 'DL999992',
                'status': 'active', 'user': self.regular_user.id},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_driver_update_as_manager(self):
        """Test driver update as manager."""
        self.authenticate(self.manager_user)
        response = self.client.patch(
            f'/api/drivers/{self.driver.id}/',
            {'status': 'inactive'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.driver.refresh_from_db()
        self.assertEqual(self.driver.status, 'inactive')

    def test_driver_delete_as_admin(self):
        """Test driver deletion as admin."""
        self.authenticate(self.admin_user)
        response = self.client.delete(f'/api/drivers/{self.driver.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Driver.objects.filter(id=self.driver.id).exists())

    def test_driver_delete_as_manager_forbidden(self):
        """Test driver deletion as manager is forbidden."""
        self.authenticate(self.manager_user)
        response = self.client.delete(f'/api/drivers/{self.driver.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TripLogAPITest(APITestCase):
    """Test Trip Logs API."""

    def setUp(self):
        User = get_user_model()

        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            email='admin@test.com',
            username='admin',
            password='admin123'
        )
        self.manager_user = User.objects.create_user(
            email='manager@test.com',
            username='manager',
            password='manager123',
            is_manager=True
        )
        self.regular_user = User.objects.create_user(
            email='user@test.com',
            username='user',
            password='user123'
        )
        self.vehicle = Vehicle.objects.create(
            model='Tata',
            registered_number='TRUCK001',
            status='active'
        )

        self.driver = Driver.objects.create(
            name='Test Driver',
            license_number='DL12345',
            status='active',
            primary_vehicle=self.vehicle
        )
        self.trip = TripLog.objects.create(
            vehicle=self.vehicle,
            driver=self.driver,
            date_time=timezone.now(),
            number_of_trips=5,
            weight=Decimal('1000.00'),
            distance_traveled=Decimal('100.00')
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_triplog_list_requires_authentication(self):
        """Test triplogs listing requires authentication."""
        response = self.client.get('/api/trip-logs/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_triplog_list_authenticated(self):
        """Test triplogs listting as authenticated."""
        self.authenticate(self.regular_user)
        response = self.client.get('/api/trip-logs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]
                         ['vehicle']['registered_number'], 'TRUCK001')

    def test_triplog_create_authenticated(self):
        """Test triplogs creation as authenticated."""
        self.authenticate(self.regular_user)
        response = self.client.post(
            '/api/trip-logs/',
            {
                'vehicle': self.vehicle.registered_number,
                'driver': self.driver.license_number,
                'date_time': timezone.now().isoformat(),
                'number_of_trips': 2,
                'weight': '100.00',
                'distance_traveled': '50.00'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TripLog.objects.count(), 2)

    def test_triplog_create_unauthenticated(self):
        """Test triplogs create as unauthenticated ."""
        response = self.client.post(
            '/api/trip-logs/',
            {
                'vehicle': self.vehicle.registered_number,
                'driver': self.driver.license_number,
                'date_time': timezone.now().isoformat(),
                'number_of_trips': 2
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_triplog_create_with_different_primary_vehicle(self):
        """Test trip log creation with different primary vehicle  to test new logic in serializer."""
        self.authenticate(self.regular_user)
        vehicle = Vehicle.objects.create(
            model='Tata',
            registered_number='TRUCK002',
            status='active'
        )
        response = self.client.post(
            '/api/trip-logs/',
            {
                'vehicle': vehicle.registered_number,
                'driver': self.driver.license_number,
                'date_time': timezone.now().isoformat(),
                'number_of_trips': 2,
                'weight': '100.00',
                'distance_traveled': '50.00'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_trip_id = response.data['id']
        response = self.client.get(f'/api/trip-logs/{new_trip_id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['vehicle']['registered_number'], vehicle.registered_number)

    def test_triplog_detail_authenticated(self):
        """Test triplogs detail as authenticated."""
        self.authenticate(self.regular_user)
        response = self.client.get(f'/api/trip-logs/{self.trip.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['vehicle']['registered_number'],
                         self.vehicle.registered_number)

    def test_triplog_update_as_regular_user_before_approval(self):
        """Test triplogs update as regular user ."""
        self.authenticate(self.regular_user)
        response = self.client.patch(
            f'/api/trip-logs/{self.trip.id}/',
            {'number_of_trips': 7},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_triplog_update_as_manager(self):
        """Test triplogs update as manager."""
        self.authenticate(self.manager_user)
        response = self.client.patch(
            f'/api/trip-logs/{self.trip.id}/',
            {'number_of_trips': 7},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.trip.refresh_from_db()
        self.assertEqual(self.trip.number_of_trips, 7)

    def test_triplog_approve_as_admin(self):
        """Test triplogs approve as admin."""
        self.authenticate(self.admin_user)
        response = self.client.post(f'/api/trip-logs/{self.trip.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.trip.refresh_from_db()
        self.assertTrue(self.trip.is_approved)

    def test_triplog_update_as_regular_user_after_approval(self):
        """Test triplogs update as regular user ."""
        self.authenticate(self.regular_user)
        sleep(2)
        response = self.client.patch(
            f'/api/trip-logs/{self.trip.id}/',
            {'number_of_trips': 7},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_triplog_approve_as_regular_user_forbidden(self):
        """Test triplogs approve as regular user is forbidden."""
        self.authenticate(self.regular_user)
        response = self.client.post(f'/api/trip-logs/{self.trip.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_triplog_calculate_weight_as_manager(self):
        """Test triplogs calculate weight as manager."""
        self.authenticate(self.manager_user)
        response = self.client.post(
            f'/api/trip-logs/{self.trip.id}/calculate/',
            {'rate': '10.50', 'calc_type': 'weight'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['amount']), float(
            Decimal('1000.00') * 5 * Decimal('10.50')))

    def test_triplog_calculate_invalid_calc_type(self):
        """Test triplogs calculate invalid calc type."""
        self.authenticate(self.manager_user)
        response = self.client.post(
            f'/api/trip-logs/{self.trip.id}/calculate/',
            {'rate': '10.50', 'calc_type': 'volume'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_triplog_calculate_requires_manager_or_admin(self):
        """Test triplogs calculation  requrie manager or admin."""
        self.authenticate(self.regular_user)
        response = self.client.post(
            f'/api/trip-logs/{self.trip.id}/calculate/',
            {'rate': '10.50', 'calc_type': 'weight'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_triplog_bulk_calculate_as_manager(self):
        """Test triplogs bulk calculate as manager."""
        self.authenticate(self.manager_user)
        TripLog.objects.create(
            vehicle=self.vehicle,
            driver=self.driver,
            date_time=timezone.now() - timedelta(days=1),
            number_of_trips=2,
            weight=Decimal('500.00'),
            distance_traveled=Decimal('20.00')
        )
        response = self.client.post(
            '/api/trip-logs/calculate-bulk/',
            {
                'start_date': (timezone.now() - timedelta(days=2)).date().isoformat(),
                'end_date': timezone.now().date().isoformat(),
                'rate': '5',
                'calc_type': 'weight'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['calc_type'], 'weight')
        self.assertGreaterEqual(response.data['total_amount'], 0.0)

    def test_triplog_bulk_calculate_invalid_date(self):
        """Test triplogs bulk calculate invalid date."""
        self.authenticate(self.manager_user)
        response = self.client.post(
            '/api/trip-logs/calculate-bulk/',
            {
                'start_date': '2025-13-01',
                'end_date': '2025-01-10',
                'rate': '5',
                'calc_type': 'weight'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_triplog_bulk_calculate_as_regular_user_forbidden(self):
        """Test triplogs bulk calculate as regular user is forbidden."""
        self.authenticate(self.regular_user)
        response = self.client.post(
            '/api/trip-logs/calculate-bulk/',
            {
                'start_date': (timezone.now() - timedelta(days=2)).date().isoformat(),
                'end_date': timezone.now().date().isoformat(),
                'rate': '5',
                'calc_type': 'weight'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class User(APITestCase):
    """Test user by admin and managers."""

    def setUp(self) -> None:
        User = get_user_model()
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            email='admin@test.com',
            username='admin',
            password='admin123'
        )
        self.manager_user = User.objects.create_user(
            email='manager@test.com',
            username='manager',
            password='manager123',
            is_manager=True
        )
        self.regular_user = User.objects.create_user(
            email='user@test.com',
            username='user',
            password='user123'
        )

    def authenticate(self, user):
        self.client.force_authenticate(user)

    def test_admin_create_user(self):
        self.authenticate(self.admin_user)

        response = self.client.post(
            '/api/users/create/',
            {
                "email": "newTest@email.com",
                "username": "newTest",
                "password": "Test@123#123"
            }
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('token', response.data)

    def test_manager_create_user(self):
        self.authenticate(self.manager_user)

        response = self.client.post(
            '/api/users/create/',
            {
                "email": "newTest@email.com",
                "username": "newTest",
                "password": "Test@123#123"
            }
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('token', response.data)

    def test_regular_user_create_user(self):
        self.authenticate(self.regular_user)

        response = self.client.post(
            '/api/users/create/',
            {
                "email": "newTest@email.com",
                "username": "newTest",
                "password": "Test@123#123"
            }
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotIn('token', response.data)
