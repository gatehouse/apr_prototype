from django.db import models
from rest_framework import serializers
from django.utils import timezone

# A request element such as 'NextPortOfCall'.
class RequestElement(models.Model):
   name = models.CharField(max_length=100, blank=False, default='')
   type = models.CharField(max_length=40, blank=False, default='')
   DataElementId = models.CharField(max_length=120, blank=False, default='')
   description = models.CharField(max_length=1000, blank=False, default='')
   
   class Meta:
      ordering = ('name', 'type', 'DataElementId', 'description')

# A port.
class Port(models.Model):
   locode = models.CharField(max_length=10, blank=False, default='')
   name = models.CharField(max_length=100, blank=False, default='')
   requestelements = models.ManyToManyField(RequestElement,
                                            through = 'RequiredInformation',
                                            through_fields = ('port', 'requestelement'))
   class Meta:
      ordering = ('locode',)

class VoyageType(models.Model):
   name = models.CharField(max_length=100, blank=False, default='')

# Relation between RequestElements and Ports.
class RequiredInformation(models.Model):
   requestelement = models.ForeignKey(RequestElement, on_delete = models.CASCADE)
   port = models.ForeignKey(Port, on_delete = models.CASCADE)
   voyagetype = models.ForeignKey(VoyageType, on_delete = models.CASCADE)
   required = models.BooleanField(blank=False, default=False)
   schedule = models.IntegerField(default = 0, blank = False)
