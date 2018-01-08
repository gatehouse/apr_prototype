import sys, json, collections, traceback, logging
from django.contrib.auth.models import User
from django.http import HttpResponse, Http404

from rest_framework import generics
from rest_framework import mixins
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from apr.apr.models import RequestElement, Port
from apr.apr.serializers import RequestElementSerializer, PortSerializer, PortSlugSerializer, PortListSerializer
from apr.apr.serializers import UserSerializer
from apr.apr.restclient import RestClient
from apr.apr.bimcoclient import BimcoClient
from apr.apr.country import get_country_name

# User

class UserViewSet(viewsets.ReadOnlyModelViewSet):
   """ 
   API endpoint that allows users to be viewed.

   retrieve:
    Return a user instance.

    list:
    Return all users.
    """
   queryset = User.objects.all()
   serializer_class = UserSerializer
   
# RequestElement

class RequestElementViewSet(viewsets.ModelViewSet):
   """
   This endpoint represents requests element such as 'NextPortOfCall'.

   retrieve: Return a request element instance.

   list: Return all request elements.

   create: Create a request element.

   delete: Delete a request element.

   update: Update a request element.

   partial_update: Update a request element.
   """
   queryset = RequestElement.objects.all()
   serializer_class = RequestElementSerializer

# Port
    
class PortList(generics.ListCreateAPIView):
   """
   This endpoint represents ports and their associated RequestElements.

   get: Return all ports.

   post: Create a port.
   """
   queryset = Port.objects.all()
   serializer_class = PortListSerializer

class PortDetail(generics.RetrieveUpdateDestroyAPIView):
   """
   This endpoint represents a port and its associated RequestElements, referenced by numeric ID.
   """
   queryset = Port.objects.all()
   serializer_class = PortSerializer
   
class PortSlugDetail(APIView):
   """
   This endpoint represents a port and its associated RequestElements, referenced by LOCODE.
   """
   def get_object(self, slug):
      try:
         return Port.objects.get(locode=slug)
      except Port.DoesNotExist:
         raise Http404

   def get(self, request, slug, format=None):
      """
      Get a port and its associated RequestElements, referenced by LOCODE.
      """
      port = self.get_object(slug)
      serializer = PortSlugSerializer(port)
      serialized_data = serializer.data
      serialized_data['requestelements'] = []
      return Response(serialized_data)

   def put(self, request, slug, format=None):
      """
      Update a port and its associated RequestElements, referenced by LOCODE.
      """
      port = self.get_object(slug)
      serializer = PortSerializer(port, data=request.data)
      if serializer.is_valid():
         serializer.save()
         return Response(serializer.data)
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

   def delete(self, request, slug, format=None):
      """
      Delete a port, referenced by LOCODE.
      """
      port = self.get_object(slug)
      port.delete()
      return Response(status=status.HTTP_204_NO_CONTENT)

class PortSlugTypeDetail(APIView):
   """
   This endpoint represents a port and its associated RequestElements, referenced by LOCODE.
   """
   def get_object(self, slug, type):
      try:
         p = Port.objects.get(locode=slug)
         return p
      except Port.DoesNotExist:
         raise Http404

   def get(self, request, slug, type, format=None):
      """
      Get a port and its associated RequestElements, referenced by LOCODE.
      """
      port = self.get_object(slug, type)
      serializer = PortSlugSerializer(port)
      serialized_data = serializer.data
      old_res = serialized_data['requestelements'];
      items = []
      for re in old_res:
         for key in re:
            if key == 'voyagetype':
               if re[key] == type:
                  # Remove voyagetype
                  nre = dict(re)
                  del nre['voyagetype']
                  items.append(nre)
      serialized_data['requestelements'] = items
      return Response(serialized_data)

   def put(self, request, slug, type, format=None):
      """
      Update a port and its associated RequestElements, referenced by LOCODE.
      """
      port = self.get_object(slug)
      serializer = PortSerializer(port, data=request.data)
      if serializer.is_valid():
         serializer.save()
         return Response(serializer.data)
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Get port info from BIMCO etc.

class PortInfoView(APIView):
   """
   Retrieve a list of known information for a port, specified by LOCODE.
   """

   def get(self, request, *args, **kwargs):
      if request.path.endswith('/'):
          locode = request.path.rsplit('/')[-3]
          imo = request.path.rsplit('/')[-2]
      else:
          locode = request.path.rsplit('/')[-2]
          imo = request.path.rsplit('/')[-1]
      if locode and imo:
         if locode == 'portinfo':
            # Missing IMO
            return Response(status = status.HTTP_400_BAD_REQUEST)
         print("Locode: %s IMO: %s" % (locode, imo))
         try:
            port = Port.objects.get(locode=locode)
         except Port.DoesNotExist:
            raise Http404
         # Get BIMCO info
         try:
            bc = BimcoClient()
            pi = bc.get_portinfo(locode, imo)
            ok = pi['success']
            
         except:
            print('BIMCO exception: %s' % sys.exc_info()[0])
            return Response({ 'error': 'Failed to get port information from BIMCO' },
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)
         print('Port Information from BIMCO: %s' % repr(pi))
         return Response({"locode": locode, "information": pi})
      else:
         return Response({"success": False})
         
# Submit ETA etc.

def is_nested_element(name):
   return (name == "gender") or (name == "nationality") or (name == "rank")

def set_nested_element(obj, name, value):
   if (name == "nationality"):
      obj["code"] = value
      c = get_country_name(value)
      if c != "":
         obj["name"] = c
   else:
      obj["name"] = value

class ShipInfoView(APIView):
   """
   """

   def copy_recursive(self, src, src_subkey, dst, dst_subkey):
      #print("----\ncopy_recursive(%s, %s)" % (repr(src), repr(dst)))
      src_val = src
      if len(src_subkey) > 0:
         src_val = src[src_subkey]
      dst_val = dst
      if len(dst_subkey) > 0:
         if not dst_subkey in dst:
            dst[dst_subkey] = {}
         dst_val = dst[dst_subkey]
      if type(src_val) is dict:
         for subkey in src_val:
            mapped_subkey = subkey[0:1].lower() + subkey[1:]
            self.copy_recursive(src_val, subkey, dst_val, mapped_subkey)
         print("copy_recursive: after recursion: %s" % repr(dst_val))
      elif type(src_val) is list:
         print("No list within list! %s" % repr(src_val))
      else:
         #print("copy_recursive: subkey %s" % dst_subkey)
         if is_nested_element(dst_subkey):
            obj = {}
            set_nested_element(obj, dst_subkey, src_val)
            dst[dst_subkey] = obj
         else:
            dst[dst_subkey] = src_val
   
   def copy_subkey(self, subkey, src, src_subkey, dst, dst_subkey):
      #print("----\ncopy_subkey('%s', %s, '%s', %s, '%s')" % (subkey, repr(src), src_subkey, repr(dst), dst_subkey))
      mapped_subkey = subkey[0:1].lower() + subkey[1:]
      if type(src[src_subkey][subkey]) is dict:
         #print("copy_subkey: %s.%s is dict" % (src_subkey, subkey))
         for subsubkey in src[src_subkey][subkey]:
            mapped_subsubkey = subsubkey[0:1].lower() + subsubkey[1:]
            #print("copy_subkey: mapped_subsubkey: %s" % mapped_subsubkey)
            if not dst_subkey in dst:
               dst[dst_subkey] = {}
            self.copy_subkey(subsubkey, src[src_subkey], subkey, dst[dst_subkey], mapped_subkey)
      elif type(src[src_subkey][subkey]) is list:
         #print("copy_subkey: %s.%s is array" % (src_subkey, subkey))
         dst[dst_subkey][mapped_subkey] = []
         for elem in src[src_subkey][subkey]:
            #print("copy_subkey: elem %s)" % elem)
            dst_elem = {}
            self.copy_recursive(elem, '', dst_elem, '')
            dst[dst_subkey][mapped_subkey].append(dst_elem)
      else:
         #print("copy_subkey: %s.%s is POD: %s" % (src_subkey, subkey, repr(src[src_subkey][subkey])))
         if not dst_subkey in dst:
            #print("copy_subkey: Create %s in %s" % (dst_subkey, repr(dst)))
            dst[dst_subkey] = {}
         #print("copy_subkey: Copy to %s.%s" % (dst_subkey, mapped_subkey))
         dst[dst_subkey][mapped_subkey] = src[src_subkey][subkey]
         #print("copy_subkey: AFTER %s" % repr(dst))
            
   def do_copy(self, j, n, response):
         
      # Traverse the tree and copy values from j to n, fixing case in the process.
      for src_key in j:
         #print("Key: %s" % src_key)
         dst_key = src_key[0:1].lower() + src_key[1:]
         
         #print("Mapped key: %s" % dst_key)
         #print("data %s" % repr(j[src_key]))
         if src_key == "$reference":
            n[src_key] = j[src_key]
         elif isinstance(j[src_key], str):
            n[dst_key] = j[src_key]
         else:
            for subkey in j[src_key]:
               #print("copy: src_key: %s subkey: %s" % (src_key, subkey))
               mapped_subkey = subkey[0:1].lower() + subkey[1:]
               #print("copy: Mapped subkey: %s" % mapped_subkey)
               #print("subkey data: %s" % repr(j[src_key][subkey]))
               if not dst_key in n:
                  #print("copy: create %s" % dst_key)
                  n[dst_key] = {}
               if not mapped_subkey in n[dst_key]:
                  n[dst_key][mapped_subkey] = {}
               #print("before copy_subkey: %s" % repr(n))
               self.copy_subkey(subkey, j, src_key, n, dst_key)
               #print("after copy_subkey: %s" % repr(n))

   def copy_portcall(self, call, n):
      if not 'Locode' in call:
         return
      if not 'port' in n:
         n['port'] = {}
      n["port"]["lastPort"] = { "locode": call["Locode"] }
      #print("copy_portcall: %s -> %s" % (repr(call), repr(n["port"]["lastPort"])))

   def copy_crewitem(self, item, n):
      # Person.Crew.Items.IdDocument -> crew.items.idDocument.name
      if not "IdDocument" in item:
         return
      n["idDocument"] = { "name": item["IdDocument"] }
      
   def copy(self, j, n, response):
      self.do_copy(j, n, response)
      #-- Special handling
      # - PortCalls
      if "PortCalls" in j:
         pc = j["PortCalls"]
         if "PortCall" in pc:
            calls = pc["PortCall"]
            print(repr(calls))
            if type(calls) is list:
               for call in calls:
                  self.copy_portcall(call, n)
         del n["portCalls"]
      # Crew
      if "Person" in j:
         p = j["Person"]
         if "Crew" in p:
            crew = p["Crew"]
            if type(crew) is list:
               i = 0
               for item in crew:
                  self.copy_crewitem(item, n["person"]["crew"][i])
                  i = i + 1
      # Type
      if "Port" in j:
         p = j["Port"]
         if "PortOfCall" in p:
            poc = p["PortOfCall"]
            if "TypeOfReporting" in poc:
               n["type"] = poc["TypeOfReporting"]
               del n["port"]["portOfCall"]["typeOfReporting"]
      # DoNotProvideWaste
      if "Waste" in j:
         w = j["Waste"]
         if "DoNotProvideWaste" in w:
            n["doNotProvideWaste"] = w["DoNotProvideWaste"]
            del n["waste"]["doNotProvideWaste"]
         if "Information" in w:
            wi = w["Information"]
            if "WasteDeliveryStatus" in wi:
               n["waste"]["wasteDeliveryStatus"] = wi["WasteDeliveryStatus"]
            del n["waste"]["information"]
      if "Port" in j:
         p = j["Port"]
         if not "port" in n:
            n["port"] = {}
         # DoNotProvideDpg
         if "DoNotProvideDpg" in p:
            n["doNotProvideDpg"] = p["DoNotProvideDpg"]
            del n["port"]["doNotProvideDpg"]
         # DoNotProvideSecurity
         if "DoNotProvideSecurity" in p:
            n["doNotProvideSecurity"] = p["DoNotProvideSecurity"]
            del n["port"]["doNotProvideSecurity"]
         # Port.PurposeOfCall.DKCode
         if "PurposeOfCall" in p:
            pop = p["PurposeOfCall"]
            if "Code" in pop:
               if not "purposeOfCall" in n["port"]:
                  n["port"]["purposeOfCall"] = {}
               n["port"]["purposeOfCall"]["code"] = pop["Code"]
            if "DKCode" in pop:
               if not "plannedOperations" in n["port"]:
                  n["port"]["plannedOperations"] = {}
               n["port"]["plannedOperations"]["code"] = pop["DKCode"]
               del n["port"]["purposeOfCall"]["dKCode"]
               if not n["port"]["purposeOfCall"]:
                  del n["port"]["purposeOfCall"]
            if "Name" in pop:
               if not "plannedOperations" in n["port"]:
                  n["port"]["plannedOperations"] = {}
               n["port"]["plannedOperations"]["description"] = pop["Name"]
               del n["port"]["purposeOfCall"]["name"]
               if not n["port"]["purposeOfCall"]:
                  del n["port"]["purposeOfCall"]
      # Waste.Items
      if "Waste" in j:
         w = j["Waste"]
         if "Items" in w:
            for i in n["waste"]["items"]:
               if "wasteType" in i:
                  waste_type = i["wasteType"]
                  i["wasteType"] = { "code": waste_type }
               if "portOfDelivery" in i:
                  port = i["portOfDelivery"]
                  i["portOfDelivery"] = { "locode": port }
      # WasteInformation
      if "WasteInformation" in j:
         wi = j["WasteInformation"]
         if "WasteDeliveryStatus" in wi:
            n["waste"]["wasteDeliveryStatus"] = wi["WasteDeliveryStatus"]
         del n["wasteInformation"]
      # Security
      if "Security" in j:
         sec = j["Security"]
         if "ShipSecurityLevel" in sec:
            n["security"]["shipSecurityLevel"] = { "name": sec["ShipSecurityLevel"] }
      # - Elements not handled by SSN
      if "ship" in n:
         del n["ship"]["company"]
         del n["ship"]["masterName"]
         del n["ship"]["deepDraught"]
         del n["ship"]["airDraught"]

         
   def post(self, request, *args, **kwargs):
      """
      Submit information from a ship to the APR.
      """
      # PortOfArrival, PortOfDeparture
      # ETA
      # ETD
      # (PositionInPortOfCall)
      # PortOfArrival.GISISCode
      # Agent.Company
      # Agent.ContactNumbers
      # Agent.ContactNumbers.BusinessTelephone
      # Agent.ContactNumbers.Telefax
      # Agent.ContactNumbers.Email
      # CallPurpose
      # CargoOverview

      try:
         log = logging.getLogger(__name__)
         
         s = request.body.decode('utf-8')
         UNICODE_BOM = u'\N{ZERO WIDTH NO-BREAK SPACE}'
         if s and s[0] == UNICODE_BOM:
            s = s[1:]
         j = json.loads(s)
         log.debug("Request body: %s" % repr(j))
         print("Request body: %s" % repr(j))
         if 'Ship.Imo' in j:
            imo = j['Ship.Imo']
         elif 'ship.Imo' in j:
            imo = j['ship.Imo']
         elif 'ship.imo' in j:
            imo = j['ship.imo']
         elif 'ship.Imo' in j:
            imo = j['ship.Imo']
         else:
            if 'Ship' in j:
               ship = j['Ship']
            elif 'ship' in j:
               ship = j['ship']
            else:
               return Response({"success": False, "error": "Missing IMO"})
            if 'imo' in ship:
               imo = ship['imo']
            elif 'Imo' in ship:
               imo = ship['Imo']
            else:
               return Response({"success": False, "error": "Missing IMO in Ship element"})
         print("IMO: %s" % imo)

         resp = { "success": True }
         rc = RestClient()
         if "$reference" in j:
            # Update existing
            ref = j["$reference"]
            n = rc.get_notification_ref(ref)
            if len(n):
               n = n[-1]
               log.debug('Existing notification %s: %s' % (ref, repr(n)))
               print('Existing notification %s: %s' % (ref, repr(n)))
               self.copy(j, n, resp)
               log.debug('Updated notification %s: %s' % (ref, repr(n)))
               print('Updated notification %s: %s' % (ref, repr(n)))
               id = rc.put_notification(n)
               resp['$reference'] = id
               print("RESP %s" % repr(resp))
            else:
               resp["error"] = "Reference not found"
         else:
            n = {}
            self.copy(j, n, resp)
            log.debug('New notification: %s' % repr(n))
            print('New notification: %s' % repr(n))
            id = rc.post_notification(n)
            log.debug('New notification has ID %s' % id)
            print('New notification has ID %s' % id)
            resp['$reference'] = id
         return Response(resp)
      except:
         traceback.print_exc(file=sys.stdout)
         print("Unexpected error: %s" % sys.exc_info()[0])
         print("Trace: %s" % repr(sys.exc_info()[2]))
         return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

   def put(self, request, *args, **kwargs):
      """
      Update information about a ship.
      """
      return self.post(request, args, kwargs)

# Browsable API

@api_view(['GET'])
def api_root(request, format=None):
   return Response({
      'users': reverse('user-list', request=request, format=format),
      'requestelement': reverse('requestelement-list', request=request, format=format),
      'port': reverse('port-list', request=request, format=format),
   })
