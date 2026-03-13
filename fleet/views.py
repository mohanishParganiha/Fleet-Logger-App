from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum, F
from .models import Vehicle, Driver, TripLog
from .serializers import VehicleSerializer, DriverSerializer, TripLogSerializer
from decimal import Decimal
from datetime import datetime
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend  # type: ignore
from .filters import TripLogFilter, VehicleFilter, DriverFilter
# Create your views here.


class LoginView(APIView):
    """login endpoint - returns auth token"""
    permission_classes = []  # allows any one to login

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {"error": "username or password cannot be empty"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(email=email, password=password)

        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {
                    "token": token.key,
                    "user_id": user.id,  # type:ignore
                    "email": user.email,
                    "is_staff": user.is_staff}
            )
        else:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )


class VehicleListCreateView(generics.ListCreateAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = VehicleFilter

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminUser()]
        return [IsAuthenticatedOrReadOnly()]


class VehicleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsAdminUser()]
        return [IsAuthenticatedOrReadOnly()]


class DriverListCreateView(generics.ListCreateAPIView):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = DriverFilter

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminUser()]
        return [IsAuthenticatedOrReadOnly()]


class DriverDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer

    def get_permissions(self):
        if self.request.method in ["PATCH", "PUT", "DELETE"]:
            return [IsAdminUser()]
        return [IsAuthenticatedOrReadOnly()]


class TripLogListCreateView(generics.ListCreateAPIView):
    queryset = TripLog.objects.all()
    serializer_class = TripLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TripLogFilter


class TripLogDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TripLog.objects.all()
    serializer_class = TripLogSerializer
    permission_classes = [IsAuthenticated]


class TripLogCalculationView(APIView):
    """calculation rate for single trip"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        # get trip object
        try:
            trip = TripLog.objects.get(pk=pk)
        except TripLog.DoesNotExist:
            return Response(
                {"error": "Trip not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # get rate and calculation type
        rate = request.data.get('rate')
        calc_type = request.data.get('calc_type')

        # **********IMP validation part **********
        # we first validate if the rate and calculation type has been provided
        if not rate or not calc_type:
            return Response(
                {"error": "Both 'rate' and 'calc_type' are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # then we check if the calculation provided matches statndard
        if calc_type not in ['weight', 'distance']:
            return Response(
                {"error": "'calc_type' must be either weight or distance"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # convert rate to decime for better accuracy
        # use try to check for invalid rates inputs such as Decimal('abc') will give type error
        try:
            rate = Decimal(rate)
        except ValueError:
            return Response(
                {"error": "enter valid rate.  interger or decimal"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if rate < 1:
            return Response(
                {"error": "rate must be greater than 0"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # finally calculation  for weight
        if calc_type == 'weight':
            # check if weight exist cause its nullable
            if trip.weight is None:
                return Response(
                    {"error": "This trip has no weight data"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            amount = trip.number_of_trips*trip.weight * rate

        # finally calculation for distance
        else:
            # check if distance exist  cause its nullable
            if trip.distance_traveled is None:
                return Response(
                    {"error": "This trip has no distance  data"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            amount = trip.number_of_trips*trip.distance_traveled * rate

        return Response(
            {
                "trip_id": trip.id,  # type: ignore
                "calc_type": calc_type,
                "rate": rate,
                "quantity_per_trip": float(
                    trip.weight if calc_type == 'weight' else trip.distance_traveled),  # type: ignore
                "total_quantity": float(
                    trip.weight*trip.number_of_trips if calc_type == "weight"  # type: ignore
                    else trip.distance_traveled * trip.number_of_trips  # type: ignore
                ),
                "amount": float(amount)
            }
        )


class TripLogBulkCalculateView(APIView):
    """calculate total rate for multiple trips in date range."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # extract the data from request
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        rate = request.data.get('rate')
        calc_type = request.data.get('calc_type')
        vehicle_number = request.data.get('vehicle')

        if not all([start_date, end_date, rate, calc_type]):
            return Response(
                {"error": "required fields are missing"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # validate calc_type
        if calc_type not in ['weight', 'distance']:
            return Response(
                {"error": "calc_type must be either 'weight' or 'distance'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # validate rate is a number
        try:
            rate = Decimal(rate)
        except ValueError:
            return Response(
                {"error": "rate must be greater than equal to 0.00 and must be integer or decimal"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if rate < 1:
            return Response(
                {"error": "rate must be greater than 0"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            start_date = datetime.fromisoformat(start_date).date()
            end_date = datetime.fromisoformat(end_date).date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if start_date > end_date:
            return Response(
                {"error": "start date cannot be greater than end date"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # filter trips from trilogs
        trips = TripLog.objects.filter(
            date_time__date__gte=start_date,
            date_time__date__lte=end_date
        )

        # filter by Vehicle if available , we can chain filters
        if vehicle_number:
            try:
                vehicle = Vehicle.objects.get(registered_number=vehicle_number)
                trips = trips.filter(vehicle=vehicle)
            except Vehicle.DoesNotExist:
                return Response(
                    {"error": f"Vehicle '{vehicle_number}' not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

        if calc_type == 'weight':
            total = trips.exclude(weight__isnull=True).aggregate(
                total=Sum(F('weight')*F('number_of_trips'))
            )['total'] or Decimal('0')
            field_name = 'total_weight'
        else:
            total = trips.exclude(distance_traveled__isnull=True).aggregate(
                total=Sum(F('distance_traveled')*F('number_of_trips'))
            )['total'] or Decimal('0')
            field_name = 'total_distance'

        amount = total*rate

        return Response(
            {
                "start_date": start_date,
                "end_date": end_date,
                "vehicle": vehicle_number,
                "total_trips": trips.count(),
                "calc_type": calc_type,
                field_name: float(total),
                "rate": float(rate),
                "total_amount": float(amount)
            }
        )
