"""apr URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from rest_framework import routers
from rest_framework.schemas import get_schema_view
from rest_framework_swagger.views import get_swagger_view
import apr.apr.views
import ship.views

router = routers.DefaultRouter()
router.register(r'users', apr.apr.views.UserViewSet)
router.register(r'requestelements', apr.apr.views.RequestElementViewSet)

schema_view = get_schema_view(title='Efficiensea 2 APR CoreAPI')
swagger_view = get_swagger_view(title='Efficiensea 2 APR Swagger API')

urlpatterns = [
    url(r'^ship/', include('ship.urls')),
    url(r'^ship/port', ship.views.get_portinfo),
    url(r'^ship/submitportinfo/$', ship.views.submit_portinfo, name='submit-portinfo'),

    url(r'^$', apr.apr.views.api_root),
    url(r'^schema/$', schema_view),
    url(r'^swagger/$', swagger_view),
    url(r'^', include(router.urls)),
    # PortInfo
    url(r"^portinfo/(?P<slug>[-\w]+)", apr.apr.views.PortInfoView.as_view()),
    # ShipInfo
    url(r"^shipinfo/$", apr.apr.views.ShipInfoView.as_view()),
    # Port
    url(r"^port/(?P<pk>\d*)/$", apr.apr.views.PortDetail.as_view()),
    url(r"^port/(?P<slug>[-\w]+)/$", apr.apr.views.PortSlugDetail.as_view()),
    url(r"^port/(?P<slug>[-\w]+)/(?P<type>[-\w]+)$", apr.apr.views.PortSlugTypeDetail.as_view()),
    url(r"^port/$", apr.apr.views.PortList.as_view(), name='port-list'),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]

