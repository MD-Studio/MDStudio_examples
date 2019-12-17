# -*- coding: utf-8 -*-

# mdstudio library imports
from mdstudio.component.session import ComponentSession
from mdstudio.api.endpoint import endpoint
from mdstudio.deferred.chainable import chainable

from time import sleep
from autobahn.wamp import RegisterOptions

DELAY = 5
POWER = 2


# The microservice API is class based and needs to inherit methods from
# the ComponentSession base class.
class RoundrobinComponent(ComponentSession):

    def authorize_request(self, uri, claims):
        # Authorize calls to API endpoints
        return True

    @endpoint('parallel', 'roundrobin_request', 'roundrobin_response',
              options=RegisterOptions(invoke=u'roundrobin'))
    def parallel_call(self, request, claims):
        """
        Parallel call

        Simulate some CPU intensive task by sleeping for 5 seconds
        then return number variable to the power of 2.
        """

        self.sleep(request['number'])
        request['number'] = request['number']**POWER
        return request

    @endpoint('sequential','roundrobin_request', 'roundrobin_response')
    def sequential_call(self, request, claims):
        """
        Sequential call

        Similar to parallel_call but without the roundrobin registration
        """

        self.sleep(request['number'])
        request['number'] = request['number']**POWER
        return request

    def sleep(self, number):

        self.log.info('Process number {0} after {1} seconds delay'.format(number, DELAY))
        sleep(5)



