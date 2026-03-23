from django.db import models

# Create your models here.

from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.conf import settings


class Equipment(models.Model):
    EQUIPMENT_TYPES = [
        ('tractor',   'Tractor'),
        ('pump',      'Water Pump'),
        ('harvester', 'Harvester'),
    ]

    user           = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name           = models.CharField(max_length=100)
    type           = models.CharField(max_length=20, choices=EQUIPMENT_TYPES)
    price_per_hour = models.IntegerField()
    location       = models.PointField(srid=4326)
    status         = models.CharField(max_length=20, default='Idle')
    is_rented      = models.BooleanField(default=False)
    current_renter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='renting_equipment'
    )
    created_at     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.location.y}, {self.location.x}"


class UserProfile(models.Model):
    ROLE_CHOICES = [('owner', 'Equipment Owner'), ('renter', 'Farmer / Renter')]

    user      = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone     = models.CharField(max_length=15)
    role      = models.CharField(max_length=10, choices=ROLE_CHOICES)
    full_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.full_name} ({self.role})"