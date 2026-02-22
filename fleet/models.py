from decimal import Decimal
from django.db import models
from django.contrib.auth.models import Permission

STATUS_CHOICES = [('active', 'Active'), ('inactive', 'Inactive')]

# Create your models here.


class Truck(models.Model):
    """Model for trucks."""
    model = models.CharField(max_length=25, blank=True)
    registered_number = models.CharField(
        max_length=10, blank=False, unique=True)
    status = models.CharField(
        max_length=10, default='active', choices=STATUS_CHOICES)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Truck: {self.registered_number}"


class Driver(models.Model):
    """Model for Drives."""
    name = models.CharField(max_length=100, blank=False)
    license_number = models.CharField(max_length=15, blank=False, unique=True)
    status = models.CharField(
        max_length=10, default='active', choices=STATUS_CHOICES)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Driver: {self.name} ({self.license_number})"


class TripLog(models.Model):
    """Models for logs."""
    date_time = models.DateTimeField(blank=False, unique=False)
    truck = models.ForeignKey(Truck, on_delete=models.CASCADE)
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

    def __str__(self):
        return f"Trip on {self.date_time} - {self.truck.registered_number}"
