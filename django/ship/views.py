import json, re
from json2html import *
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.http import HttpResponse, HttpResponseBadRequest, Http404
from django import forms
from apr import secrets
from apr import settings
from apr.apr import restclient
from apr.apr.models import Port
from apr.apr.serializers import ShowPortInfoSerializer
import requests
from requests.auth import HTTPBasicAuth
from .forms import GetPortInfo
from .forms import SubmitPortInfo

def index(request):
    return HttpResponse("Hello, world. You're at the ship index.")

def get_portinfo(request):
    if request.method == "POST":
        print("get_portinfo POST: %s" % repr(request.POST))
        form = GetPortInfo(request.POST)
        if form.is_valid():
            slug = form.cleaned_data['port']
            url = request.scheme+'://'+settings.APR_CONFIG['APR_BASE_URL']+'/portinfo/' + slug.upper() + '/'
            print("get_portinfo URL: %s" % url)
            r = requests.get(url,
                             auth=HTTPBasicAuth(secrets.APR_SECRETS['APR_USER'],
                                                secrets.APR_SECRETS['APR_PASS']))
            if r.status_code != 200:
                return HttpResponse("Cannot find port %s: %d" % (slug, r.status_code))

            port_html = mark_safe(json2html.convert(r.json()))

            r = requests.get(request.scheme+'://'+settings.APR_CONFIG['APR_BASE_URL']+'/port/' + slug.upper() + '/',
                             auth=HTTPBasicAuth(secrets.APR_SECRETS['APR_USER'],
                                                secrets.APR_SECRETS['APR_PASS']))
            if r.status_code != 200:
                return HttpResponse("Cannot find port %s" % slug)

            re = r.json()['requestelements']
            if not re:
                return HttpResponse("Cannot find requestelements for port %s" % slug)

            print("\nget_portinfo: Render")
         
            return render(request, 'showportinfo.html', {
                'serializer': ShowPortInfoSerializer(),
                'port': slug.upper(),
                'portinfo': port_html,
                'requestelements': re,
            })
    else:
        form = GetPortInfo()

    return render(request, 'portinfo.html',
                  { 'form': form,
                    'base_url': request.scheme + '://' + settings.APR_CONFIG['APR_BASE_URL']
                  })

def submit_portinfo(request):
    print("submit_portinfo")
    if request.method == "POST":
        print("submit_portinfo POST: %s" % repr(request.POST))
        imo = ''
        port_locode = ''
        port_name = ''
        for v in request.POST:
            if v == 'port_locode':
                port_locode = request.POST[v].upper()
            elif v == 'Ship identification.IMO number':
                imo = request.POST[v]
        try:
            p = Port.objects.get(locode=port_locode)
            port_name = p.name
        except Port.DoesNotExist:
            return render(request, 'submittedportinfo.html', { 'status': 'Port \'%s\' does not exist' % port_locode })
        
        print("IMO %s" % imo)
        shipinfo = { 'IMONumber': imo }
        #try:
        rc = restclient.RestClient()
        print("Get notification")
        n = rc.get_notification(shipinfo)
        print("Got %d notifications" % len(n))
        if not n:
            return render(request, 'submittedportinfo.html', { 'status': 'No notifications found' })
        n = n[0] #!!
        print(repr(n['port']))
        print(repr(n['port']['portOfCall']))
        print(repr(n['port']['portOfCall']['locode']))
        #n['port']['portOfCall']['locode'] = request.POST['re_NextPortOfCall']
        n['port']['portOfCall'] = { 'locode': port_locode, 'name': port_name }
            
        rc.put_notification(n)
        print("Sent notification")
            
        return render(request, 'submittedportinfo.html', { 'status': 'OK' })
        #except:
        #    return render(request, 'submittedportinfo.html', { 'status': 'Errors: %s' % repr(sys.exc_info()) })
         
    else:
       port = request.GET['port']
       form = SubmitPortInfo(elements = request.GET['requestelements'], port = port)
       return render(request,
                     'submitportinfo.html',
                     {
                         'port': port,
                         'form': form,
                         'base_url': request.scheme + '://' + settings.APR_CONFIG['APR_BASE_URL']
                     })
