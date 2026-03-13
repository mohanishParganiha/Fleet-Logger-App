from django.db import models
from users.models import User

STATUS_CHOICES = [('active', 'Active'), ('inactive', 'Inactive')]

# Create your models here.


class Vehicle(models.Model):
    """Model for Vehicles."""
    model = models.CharField(max_length=25, blank=True)
    registered_number = models.CharField(
        max_length=10, blank=False, unique=True)
    status = models.CharField(
        max_length=10, default='active', choices=STATUS_CHOICES)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-status', 'registered_number', '-date_created']

    def __str__(self):
        return f"Vehicle: {self.registered_number}"


class Driver(models.Model):
    """Model for Drives."""
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='driver_profile',
        blank=True,
        null=True,
        help_text='link to user account if driver needs login access'
    )
    name = models.CharField(max_length=100, null=False,
                            blank=False, unique=False)
    license_number = models.CharField(max_length=15, blank=False, unique=True)
    status = models.CharField(
        max_length=10, default='active', choices=STATUS_CHOICES)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-status', 'name', '-date_created']

    def __str__(self):
        return f"Driver: {self.name} ({self.license_number})"


class TripLog(models.Model):
    """Models for logs."""
    date_time = models.DateTimeField(blank=False, unique=False)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    number_of_trips = models.IntegerField(blank=False)
    weight = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True)
    distance_traveled = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    pick_up = models.CharField(max_length=100, blank=True, null=True)
    drop_off = models.CharField(max_length=100, blank=True, null=True)
    diesel_fill = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True)

    class Meta:
        ordering = ['-date_time']

    def __str__(self):
        return f"Trip on {self.date_time} - {self.vehicle.registered_number}"
