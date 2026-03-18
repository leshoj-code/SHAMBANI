from django.db import models

# Create your models here.

from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Equipment(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    EQUIPMENT_TYPES = [
        ('tractor', 'Tractor'),
        ('pump', 'Water Pump'),
        ('harvester', 'Harvester'),
    ]
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=EQUIPMENT_TYPES)
    price_per_hour = models.IntegerField() # In KES
    # srid=4326 is the standard for GPS (WGS84)
    location = models.PointField(srid=4326) 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.location.y}, {self.location.x}"
    
    is_rented = models.BooleanField(default=False) 
    # Who is renting it?
    current_renter = models.CharField(max_length=100, blank=True, null=True)

    owner_phone = models.CharField(max_length=15, default="254700000000")
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)

    status = models.CharField(max_length=20, default='Idle')
    current_renter = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='renting_equipment'
    )
    