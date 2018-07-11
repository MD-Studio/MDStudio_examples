# Building MDStudio microservices

With MDStudio we went a long way to make writing microservices an easy task
and it should be as you should focus on writing functional code and leave
the infrastructure to us.

The examples in this directory will guide you in setting up the thin layer
around your code to expose its functionality as microservice endpoints in
the MDStudio environment.
Although the JSON based WAMP communication protocol is available in nearly
12 different [languages](https://crossbar.io/about/Supported-Languages/)
we prefer Python.

Python is by far the most feature rich WAMP implementation with extensive
authentication, authorization and security support. It is also easy to
bind to other languages and therefor it should sufficiently cover most
applications.

We like Python allot and given that the Crossbar microservice broker is
also written in Python we extended the Python WAMP interface with
additional features to make the framework even more flexible, secure and
easy to use. These features are often not availble for WAMP implementations
written in other languages. You can still use them to call endpoints on
other microservices but exposing new endpoints is limited.
Ever the more reason to learn Python for now!