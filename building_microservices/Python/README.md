# Writing Python based microservices

Using Python is by far the easiest and most feature rich way of writing microservices
for the MDStudio environment. It reassembles writing a small Python package with
similar structure and convenient installation and distribution support.

The examples in this directory will guide you through the steps of setting up the
basic skeleton of a MDStudio microservice, adding functional endpoints and using some
of the advanced options in the MDStudio framework.

We will start with the compulsary `hello world` example and then move on to more
advanced examples.

### Entry-level knowledge
Basic knowledge of the Python language and some understanding of the concept of
asynchronous or event driven programming if sufficient to start coding.

In addition you should be familiar with the [JSON format](https://en.wikipedia.org/wiki/JSON)
and [JSON Schema](http://json-schema.org) as formal way to describe the data in a
JSON document.

### Requirements
The mdstudio library is the only Python package that is required. It is a subpackage of
the main [MDStudio](https://github.com/MD-Studio/MDStudio) framework that you should have
installed on your machine by now.

The mdstudio library is in `~/MDStudio/mdstudio`. You should install it in the PYTHONPATH
of the Python distribution you intend to write the microservice in. Python versions 2.7,
3.6 and up are supported.

**Note:**
The mdstudio library relies on files in the main MDStudio framework folder and therefor it
needs to be installed `in-place` using the `-e` option of pip:

    >> pip install -e mdstudio/


## Example 1: A "Hello World" microservice

The "Hello World" microservice is a very basic microservice that exposes one endpoint
that, when called, returns a "hello world" message with a time stamp.
Although not a very exiting result it illustrates the basic framework of a Python
microservice that will serve as the blueprint for all the other examples.

The `~/hello_world` directory contains the example code. Let's go through it step-by-step.


### 1: Directory structure

The directory structure of a Python component reassembles that of a Python package.
There is plenty of information available online such as [here](http://python-packaging.readthedocs.io/en/latest/)
As a minimum that directory should have the following structure (as for the hello_world
example):

    hello_world/
        hello_world/
            schemas/
                endpoints/
                    hello.request.v1.json
                    hello.response.v1.json
                resources/
                    hello-message.v1.json
            __init__.py
            __main__.py
            application.py
        settings.yml
        setup.py

- The top-level directory contains all package data and may have an arbitrary name. In this
  case it is named the same way as the actual package one level down (`hello_world`)
- The `setup.py` file is the main file with all information on how to install the package in the
  users Python environment. It is a regular Python file where `setuptools` is imported and used
  to install the package. The information used for installation is represented as Python dictionary.
  Package installation tools such as [pip](https://packaging.python.org/tutorials/installing-packages/)
  also make use of this. Setup.py is also the file where you want to list any Python package dependencies
  that your code might have in particular when these dependencies are hosted on the
  [Python Package Index](https://pypi.org) in case of which they will be resolved automatically at
  installation time.
- The `settings.yml` (a YAML file) contains the default settings of the component. More on them below.
- The `hello_world` sub directory contains the actual package code which equals the distribution name
  as defined in `setup.py`.
- Inside the `hello_world` package directory there should be an `__init__.py` file necessary for Python to
  recognize it as a package. It should ideally remain empty. There is also a `__main__.py` that contains
  the startup script for the component.
- The `application.py` (or any other name) contains the actual microservice API interface with endpoints
  it exposes.
- The `schemas` directory is something you normally do not find in a Python package. It contains the
  JSON schemas that describe the input (\*.request.v1.json) and output (\*.response.v1.json) of a
  microservice endpoint. A JSON schema contains meta-data describing a JSON construct, the message format
  that is been send between microservice endpoints. A JSON schema describes the parameters that an endpoints
  accepts and returns, what type and format they have, there default value, if they are required or not and
  so on. These schema's are used to inform the user on the requirements of an endpoint and to validate the
  data passed between them.
  When a microservice registers itself with the MDStudio broker the schema definitions are registered by a
  special `schema` microservice that is part of the MDStudio core framework. Central registration enables the
  MDStudio broker to validate all messages passed between microservices and potentially allows schemas to be
  reused by others. The schema registration supports visioning (hence the `v1` in the schema name) that
  allows for a degree of backwards compatibility when newer versions of a microservice are released.

### The HelloWorld microservice API
The `application.py` file is where all the magic happens, let's open it and have a look at what happens.

At the top of the Python file we are importing methods from the mdstudio library. The required ones here are:

- `ComponentSession` from mdstudio.component.session is the base class that contains all methods required to
  register the microservice and it's endpoints with the MDStudio broker, handle authentication and authorization,
  establish communication and provide convenience methods such as loggers and database access.
  In our hello world API class (HelloWorldComponent) we inherit the methods from this base class.
- `endpoint` from mdstudio.api.endpoint is a Python [decorator](https://wiki.python.org/moin/PythonDecorators)
  that "decorates" the class methods that we will assign as microservice endpoints in our hello world API.
  The decorator takes care of registering the methods as endpoints with MDStudio broker and linking the JSON
  schemas describing endpoint input and output to the method.

The `HelloWorldComponent` class contains the API endpoint methods of our hello world microservice. It inherits
from the `ComponentSession` base class as mentioned above. The minimal but functional API thus becomes:

    class HelloWorldComponent(ComponentSession):

        def ...

**Authentication and Authorization**

The first method we need to implement (or actually override) is the `authorize_request` method.
MDStudio supports fine grained authentication and authorization functionality in a multi-user settings such as
authorization on user, role or group level or a custom method.

Authorization happens in two phases: in the core of the MDStudio application, and in the microservice that is called.
At the microservice side this is enabled by the `authorize_request` method that returns `False` by default
(not authorized). We override the method and simly return `True` stating that calls to the API endpoints are
always allowed.

Custom claims can be made by the caller of your endpoint. These claims are signed and verified by the Authorization
component automatically, so that you are sure that they are not spoofed once you receive them.
You can then use them for custom authorization.


**Microservice start-up procedures**

When a microservice is starting up, has successfully authenticated and authorized with the broker and registered
its methods the `on_run` method is called. This is an optional method to implement but can be useful to execute
any initiation routines your service might require.

In our "Hello World" example we are using the method to call the hello endpoint on our own microservice to
illustrate how to call other endpoints and deal with asynchronous nature of these calls.
More on these topics follows below


**Endpoint registration**

The "Hello World" microservice registers a single endpoint that accepts an arbitrary message from the user and
returns that message in a 'hello world' string and the time it took to reply.
Exposing the method that performs these functions as API endpoint requires nothing more that adding the `endpoint`
decorator as:

    `@endpoint({uri}, {input-schema}, {output-schema})`

Where:
- `uri`: is the endpoint name in the fully qualified uri that uniquely identifies the method in the microservice
  environment. We named our method 'hello' and it can be called using the fully qualified uri
  `mdgroup.echo.endpoint.hello` following the syntax `{vendor}.{component}.endpoint.{uri}`. The method name
  happens to be the same as the endpoint name but this is not a requirement.
- `input-schema`: is the name of the JSON schema that describes the input to the method. It is required.
  This would point to the `hello-request.v1.json file the /schemas/endpoints directory. The schema definitions
  can also be defined inline, `{'type': 'null'}` if the function does not require input (status endpoints).
- `output-schema`: is the name of the JSON schema that describes the output the method returns similar to the
  `input-schema`.

When the endpoint is called the decorator verifies the permissions, validates the request with the `{input-schema}`,
and validating the output with the `{output-schema}`.


**Settings**
Microservices are independant and therefor share no global configuration variable.
For service-specific configuration and session configuration (details for automatic login), you can use all or any of
- settings.json
- .settins.json
- settings.yml
- .settings.yml

They are loaded in this order, and each next file overwrites and extends settings from the previous.
These can also be overridden for development by
- settings.dev.json
- .settings.dev.json
- settings.dev.yml
- .settings.dev.yml

The dot-prefixed settings are not committed, and should be used for production settings that should not be shared
through git.

The settings are loaded into the `ComponentSession` in the variable `self.component_config`, with three sections:
`static`, `session`, `settings`.
- The `session` section is used for session-specific configuration, such as login details
- The `static` section is used for vendor-defined (the component developer) settings.
- The `settings` section is intended for component settings that are variable and can be changed.


**Logging in microservices**

There is probably no need to explain the importance of informative logging in software development.
This is certainly true for distributed applications where a log contains the combined entries of various
potentially distributed service endpoints.

MDStudio features a logging microservice with log aggregation as part of the core. The `ComponentSession`
instantiates a Python `logging` instance for you automatically (`self.log`). This is a structured logger
that logs to the 'log' microservice.


### Calling methods
In the example, the component calls itself once the registration is complete, by scheduling the call two seconds later with `call_later(2, call_hello)`.

    @chainable
    def call_hello(self):
        with self.group_context('mdgroup'):
            send_time = now()
            response = yield self.call('mdgroup.echo.endpoint.hello', {
                'message': {
                    'greeting': 'Hello World!',
                    'sendTime': send_time
                }
            })

A few things happen here: the context is switched from the default user context for calling to the group context of `mdgroup`.
This makes sure that you are authorized to call the endpoint as the given group, and sign the group into your claims.
The context is automatically restored after the indented `with` codeblock, even if the call fails.

#### Chainable
The `@chainable` decorator is an extension of (and should therefore be preferred over) the previously used `@inlineCallbacks`.
Functions wrapped in chainable support the `yield` syntax, as well as chaining methods with the result.
For example:

    # call('some.uri') result:
    # {
    #     'property': {
    #         'nested-property': {
    #             'value': 0
    #         }
    #     }
    # }

    # old style
    @inlineCallbacks
    def first_method():
        result = yield call('some.uri')
        returnValue(result['property'])

    @inlineCallbacks
    def second_method():
        result = yield first_method()
        calculated_value = result['nested-property'] + 1
        returnValue(calculated_value)


    # new style
    def first_method():
        result = call('some.uri')
        return result['property']  # this is chained to the Chainable result of `call`

    @chainable
    def second_method()
        calculated_value = (yield first_method()['nested-property']) + 1

        return_value(calculated_value)

This example is not to promote the style of `call` without `yield`, but to demonstrate the power of chaining.
It is now not always necessary to use the decorator, even when we need to extract something from a deferred result!
Everything you need for this is defined in the `mdstudio` library.

### Running your component
For running your component, you need a (very small) `__main__.py` script, containing the following.

    from mdstudio.runner import main
    from my_component.application import MyComponent

    if __name__ == '__main__':
        main(MyComponent)

That's it! You can now install your component and run it!

    >>> pipenv shell
    >>> pip install -e components/my_component
    >>> python -m my_component


