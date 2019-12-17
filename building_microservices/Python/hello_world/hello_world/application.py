# -*- coding: utf-8 -*-

# mdstudio library imports
from mdstudio.component.session import ComponentSession
from mdstudio.api.endpoint import endpoint
from mdstudio.deferred.call_later import call_later
from mdstudio.deferred.chainable import chainable
from mdstudio.utc import now, from_utc_string

from pprint import pprint


# The microservice API is class based and needs to inherit methods from
# the ComponentSession base class.
class HelloWorldComponent(ComponentSession):

    def authorize_request(self, uri, claims):
        # Authorize calls to API endpoints
        return True

    def on_run(self):
        """
        on_run

        Optional method, called when the microservice first registered
        with the MDStudio broker. It can be used to run initiation routines
        """

        call_later(2, self.call_hello)
        print('Waiting a few seconds for things to start up')

    @endpoint('hello', 'hello_request', 'hello_response')
    def hello(self, request, claims):
        """
        hello endpoint

        Accepts a 'request' dictionary as described by the hello-request.v1.json
        schema in <package>/schema/endpoints and returns a response dictionary
        described by hello-response.v1.json

        The response consist of the recieved message prefixed with 'Hello World!'
        and a return time stamp.
        """

        # Service specific settings as defined in the package settings.*.yml/json are
        # exposed in self.component_config.settings
        if self.component_config.settings['printInEndpoint']:
            self.log.info('Endpoint request object:')
            pprint(request)

        return_time = now()

        # The 'sendTime' argument is not required. Set to current time if not provided
        if 'sendTime' not in request:
            self.log.info('No "sendTime" argument in request, set to current time')
            send_time = return_time
        else:
            send_time = from_utc_string(request['sendTime'])

        # Reuse the request dictionary as response
        request['greeting'] = 'Hello World!: {0}'.format(request['greeting'])
        request['sendTime'] = send_time.isoformat()
        request['returnTime'] = return_time.isoformat()

        # Log the call delay
        self.report_delay('User -> Component', return_time - send_time)

        if self.component_config.settings['printInEndpoint']:
            self.log.info('Endpoint response object:')
            pprint(request)

        # Return the request dictionary. This will be validated against the
        # hello-response.v1.json JSON schema
        return request

    @chainable
    def call_hello(self):
        """
        call_hello

        Calling the 'hello' endpoint on our own microservice.
        """

        send_time = now()
        response = yield self.group_context('mdgroup').call('mdgroup.hello_world.endpoint.hello', {
            'greeting': 'Calling self',
            'sendTime': send_time
        })

        # Reporting some delay times of the round call
        receive_time = now()
        return_time = from_utc_string(response['returnTime'])

        self.report_delay('Component -> User', receive_time - return_time)
        self.report_delay('Total', receive_time - send_time)

    def report_delay(self, delay_type, delay):

        self.log.info('{delay_type:>20} delay: {delay:>8.2f} ms',
                      delay_type=delay_type,
                      delay=delay.total_seconds() * 1000)
