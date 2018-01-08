# apr_prototype

This is a prototype of the Automatic Port Reporting (APR) system, part of the EfficienSea2 project.

The prototype is implemented using [Django](https://www.djangoproject.com/) and
[Django REST Framework](http://www.django-rest-framework.org/). This means that it requires [Python](https://www.python.org/) to run.

The APR consist of three logical parts:

1. A database which associates a *port* with a list of *request elements*. For each association, a flag indicates
whether the element is *required*, and a number indicates how many hours prior to arrival/departure it must be sent.
The database is exposed via a REST API (web service), intented to facilitate building a graphical application for data
entry. (Such an application has been developed during the project, but is not contained in this repository, as it is not
open source).

2. An API for retrieving information about a port. This information is retrieved from another set of web services
provided by BIMCO.

3. An API for submitting information to a port. In the current version of the prototype, the information is simply
forwarded to the Danish National Single Window (SafeSeaNet) after being converted to an appropriate format.

---

This project has received funding from the European Union's Horizon 2020 research and innovation programme under grant agreement No 636329.
