from django.contrib.auth.models import User
from apr.apr.models import RequestElement, Port, RequiredInformation, VoyageType
from rest_framework import serializers
from django.db import transaction
import sys

class UserSerializer(serializers.HyperlinkedModelSerializer):
   class Meta:
      model = User
      fields = ('url', 'username', 'email')

class RequiredInformationSerializer(serializers.ModelSerializer):
   name = serializers.ReadOnlyField(source = 'requestelement.name')
   type = serializers.ReadOnlyField(source = 'requestelement.type')
   DataElementId = serializers.ReadOnlyField(source = 'requestelement.DataElementId')
   description = serializers.ReadOnlyField(source = 'requestelement.description')
   voyagetype = serializers.SlugRelatedField(slug_field='name', read_only=True)

   class Meta:
      model = RequiredInformation
      fields = ('name', 'type', 'DataElementId', 'schedule', 'voyagetype', 'required', 'schedule', 'description')

class RequestElementSerializer(serializers.ModelSerializer):

   class Meta:
      model = RequestElement
      fields = ('id', 'name', 'type', 'DataElementId', 'description')

class RequiredInformationSerializerShort(serializers.ModelSerializer):
   name = serializers.ReadOnlyField(source = 'requestelement.name')
   type = serializers.ReadOnlyField(source = 'requestelement.type')

   class Meta:
      model = RequiredInformation
      fields = ('name')

class ShowPortInfoSerializer(serializers.ModelSerializer):
   requestelements = RequiredInformationSerializerShort(source = 'requiredinformation_set', many = True)
   class Meta:
      model = Port
      fields = ('id', 'requestelements')
   
class PortSerializer(serializers.ModelSerializer):
   requestelements = RequiredInformationSerializer(source = 'requiredinformation_set', many = True)

   class Meta:
      model = Port
      fields = ('id', 'locode', 'name', 'requestelements')
      lookup_field = 'locode'

   def create(self, validated_data):
      print("create: %s" % validated_data)
      requestelements_data = validated_data.pop('requiredinformation_set')
      port = Port.objects.create(**validated_data)
      for requestelement_data in requestelements_data:
         RequestElement.objects.create(port=port, **requestelement_data)
      return port

   @transaction.atomic
   def update(self, instance, validated_data):
      '''
      Customize the update function for the serializer to update the
      related_field values.
      '''

      if 'requiredinformation_set' in validated_data:
         instance = self._update_requiredinformation(instance, validated_data)

         # remove requestelements key from validated_data to use update method of
         # base serializer class to update model fields
         validated_data.pop('requiredinformation_set', None)

      return super(PortSerializer, self).update(instance, validated_data)


   def _update_requiredinformation(self, instance, validated_data):
      '''
      Update requiredinformation data for a port.
      '''
      requestelements = self.initial_data.get('requestelements')
      if isinstance(requestelements, list) and len(requestelements) >= 1:
         # make a set of incoming requestelements
         incoming_requestelement_ids = list()

         for member in requestelements:
               di = member['DataElementId']
               try:
                  re = RequestElement.objects.get(DataElementId=di)
               except:
                  print("Exception: %s" % sys.exc_info()[0])
                  raise serializers.ValidationError(
                     'The specified DataElementId does not exist, or is not unique.'
                  )
               try:
                  v_type = member['voyagetype']
                  vt = VoyageType.objects.get(name=v_type)
               except:
                  print("Exception: %s" % sys.exc_info()[0])
                  raise serializers.ValidationError(
                     'The specified VoyageType does not exist, or is not unique.'
                  )
               item = {
                  'id': re.id,
                  'required': member['required'],
                  'schedule': member['schedule'],
                  'voyagetype_id': vt.id
               }
               incoming_requestelement_ids.append(item)

         RequiredInformation.objects.filter(
            port_id=instance.id
         ).delete()

         RequiredInformation.objects.bulk_create(
            [
               RequiredInformation(
                  port_id=instance.id,
                  requestelement_id=requestelement['id'],
                  required=requestelement['required'],
                  schedule=requestelement['schedule'],
                  voyagetype_id=requestelement['voyagetype_id'],
               )
               for requestelement in incoming_requestelement_ids
            ]
         )
         return instance
      else:
         raise serializers.ValidationError('requestelements is not a list of objects' )

class PortSlugSerializer(serializers.ModelSerializer):
   requestelements = RequiredInformationSerializer(source = 'requiredinformation_set', many = True)
   class Meta:
      model = Port
      fields = ('id', 'locode', 'name', 'requestelements')
      lookup_field = 'locode'

class PortListSerializer(serializers.ModelSerializer):
   class Meta:
      model = Port
      fields = ('id', 'locode', 'name')
      lookup_field = 'locode'
