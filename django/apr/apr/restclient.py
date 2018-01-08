from io import BytesIO
import coreapi
from django.conf import settings
from apr import secrets
import pycurl, json

class RestClient:
   def __init__(self):
      self.base_url = '%s/api/v1' % settings.APR_CONFIG['SSN_BASE_URL']
      self.auth = '%s:%s' % (secrets.APR_SECRETS['SSN_USER'], secrets.APR_SECRETS['SSN_PASS'])

   def get_notifications(self):
      buffer = BytesIO()
      c = pycurl.Curl()
      c.setopt(c.URL, '%s/search?query=contentType:notification' % self.base_url)
      c.setopt(c.WRITEDATA, buffer)
      c.setopt(c.SSL_VERIFYHOST, False)
      c.setopt(c.SSL_VERIFYPEER, False)
      c.setopt(c.HTTPAUTH, c.HTTPAUTH_NTLM)
      c.setopt(c.USERPWD, self.auth)
      c.setopt(c.FOLLOWLOCATION, True)
      c.perform()
      ec = c.getinfo(c.RESPONSE_CODE)
      c.close()
      if ec != 200:
         print("get_notifications HTTP error: %d" % ec)
         return

      data = buffer.getvalue().decode('iso-8859-1')
      j = json.loads(data)
      print(json.dumps(j, indent=4, sort_keys=True))

   def get_notification_filter(self, filter):
      buffer = BytesIO()
      c = pycurl.Curl()
      url = '%s/search?query=contentType:notification%%20AND%%20%s' % (self.base_url, filter)
      print("SSN URL: %s" % url)
      c.setopt(c.URL, url)
      c.setopt(c.WRITEDATA, buffer)
      c.setopt(c.SSL_VERIFYHOST, False)
      c.setopt(c.SSL_VERIFYPEER, False)
      c.setopt(c.HTTPAUTH, c.HTTPAUTH_NTLM)
      c.setopt(c.USERPWD, self.auth)
      c.setopt(c.FOLLOWLOCATION, True)
      c.perform()
      ec = c.getinfo(c.RESPONSE_CODE)
      c.close()
      if ec != 200:
         raise Exception("Error fetching SSN notification: %d" % ec)

      data = buffer.getvalue().decode('iso-8859-1')
      j = json.loads(data)
      return j['results']

   def get_notification(self, shipInfo):
      filter = ''
      if 'MMSINumber' in shipInfo:
         filter = 'ship.mmsi:%%20%s' % shipInfo.MMSINumber
      elif 'IMONumber' in shipInfo:
         filter = 'ship.imo:%%20%s' % shipInfo['IMONumber']
      elif 'CallSign' in shipInfo:
         filter = 'ship.callSign:%%20%s' % shipInfo.CallSign
      elif 'ShipName' in shipInfo:
         filter = 'ship.name:%%20%s' % shipInfo.ShipName
      else:
         raise Exception("Error: Nothing to search for")
      return self.get_notification_filter(filter)
      
   def get_notification_imo(self, imo):
      filter = 'ship.imo:%%20%s' % imo
      return self.get_notification_filter(filter)
      
   def get_notification_ref(self, ref):
      filter = '$reference:%%20%s' % ref
      return self.get_notification_filter(filter)
      
   def put_notification(self, record):
      if not '$reference' in record:
         raise Exception("Error posting SSN notification: No $reference field")
      ref = record['$reference']
      print("put_notification: Reference %s" % ref)
      buffer = BytesIO()
      c = pycurl.Curl()
      url = '%s/content/notification/%s' % (self.base_url, ref)
      c.setopt(c.URL, url)
      c.setopt(c.WRITEDATA, buffer)
      c.setopt(c.SSL_VERIFYHOST, False)
      c.setopt(c.SSL_VERIFYPEER, False)
      c.setopt(c.HTTPAUTH, c.HTTPAUTH_NTLM)
      c.setopt(c.USERPWD, self.auth)
      c.setopt(c.FOLLOWLOCATION, True)
      c.setopt(c.HTTPHEADER, ['Accept: application/json', 'Content-Type: application/json'])
      c.setopt(c.CONNECTTIMEOUT, 60)
      c.setopt(c.TIMEOUT, 120)
      c.setopt(c.POST, 1)
      print("JSON is %s" % json.dumps(record))
      c.setopt(c.POSTFIELDS, json.dumps(record))
      print('Calling SSN...')
      c.perform()
      ec = c.getinfo(c.RESPONSE_CODE)
      print('Done calling SSN')
      c.close()
      if ec != 200:
         print("Error: %d" % ec)
         #return
      data = buffer.getvalue().decode('iso-8859-1')
      #print('PUT: %s' % data)
      print('REF: %s' % ref)
      return ref
      
   def post_notification(self, record):
      buffer = BytesIO()
      c = pycurl.Curl()
      url = '%s/content/notification' % self.base_url
      c.setopt(c.URL, url)
      c.setopt(c.WRITEDATA, buffer)
      c.setopt(c.SSL_VERIFYHOST, False)
      c.setopt(c.SSL_VERIFYPEER, False)
      c.setopt(c.HTTPAUTH, c.HTTPAUTH_NTLM)
      c.setopt(c.USERPWD, self.auth)
      c.setopt(c.FOLLOWLOCATION, True)
      c.setopt(c.HTTPHEADER, [
         'Accept: application/json',
         'Content-Type: application/json',
         'ssn-client-schema-version: 3.5.0'
      ])
      c.setopt(c.CONNECTTIMEOUT, 60)
      c.setopt(c.TIMEOUT, 120)
      c.setopt(c.POST, 1)
      record["contentType"] = "notification"
      print("----\nSending to SSN: %s" % json.dumps(record))
      c.setopt(c.POSTFIELDS, json.dumps(record))
      print('Calling SSN...')
      c.perform()
      ec = c.getinfo(c.RESPONSE_CODE)
      print('Done calling SSN')
      c.close()
      if ec != 200:
         print("Error: %d" % ec)
         #return
      data = buffer.getvalue().decode('iso-8859-1')
      print('----\nReturned from SSN: %s' % data)
      j = json.loads(data)
      if not '$reference' in j:
         raise Exception("Error posting SSN notification: No $reference field")
      return j['$reference']

   
