from io import BytesIO
import coreapi, datetime
from django.conf import settings
from apr import secrets
import pycurl, json

class BimcoClient:
   def __init__(self):
      self.base_url = 'https://portinformationservice.bimco.org/api/portinformation/'
      self.auth = 'Pp9xXHE3g5rFgzKw'

   def get_portinfo(self, locode, imo):
      buffer = BytesIO()
      c = pycurl.Curl()
      year = datetime.datetime.now().year
      c.setopt(c.URL, '%s/%s/%s/%d/%s' % (self.base_url, 'PortWorkingHours', locode, year, imo))
      c.setopt(c.WRITEDATA, buffer)
      c.setopt(c.FOLLOWLOCATION, True)
      c.setopt(c.SSL_VERIFYHOST, False)
      c.setopt(c.SSL_VERIFYPEER, False)
      c.setopt(c.HTTPHEADER, [ 'Authorization: %s' % self.auth ])
      c.perform()
      ec = c.getinfo(c.RESPONSE_CODE)
      c.close()
      if ec != 200:
         print("Error: %d" % ec)
         return { 'success': False }

      data = buffer.getvalue().decode('utf-8')
      j = json.loads(data)
      if not j['Success']:
         return { 'success': False }

      working_hours = j['Information']
      
      buffer = BytesIO()
      c = pycurl.Curl()
      c.setopt(c.URL, '%s/%s/%s/%s' % (self.base_url, 'documents', locode, imo))
      c.setopt(c.WRITEDATA, buffer)
      c.setopt(c.FOLLOWLOCATION, True)
      c.setopt(c.SSL_VERIFYHOST, False)
      c.setopt(c.SSL_VERIFYPEER, False)
      c.setopt(c.HTTPHEADER, [ 'Authorization: %s' % self.auth ])
      c.perform()
      ec = c.getinfo(c.RESPONSE_CODE)
      c.close()
      if ec != 200:
         print("Error: %d" % ec)
         return { 'success': False }

      data = buffer.getvalue().decode('utf-8')
      j = json.loads(data)

      docs = j['Information']
      
      return { 'working_hours': working_hours, 'documents': docs, 'success': True }
