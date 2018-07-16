# -*- coding: utf-8 -*-

import time

from mdstudio.deferred.chainable import chainable
from mdstudio.component.session import ComponentSession
from mdstudio.runner import main


class UserSession(ComponentSession):
    """
    MDStudio session for interacting with the 'roundrobin' microservice.
    """

    init_time = None

    def authorize_request(self, uri, claims):
        return True

    def append(self, result, number):

        result = result['number']
        print('Result {0} for {1} after {2} seconds'.format(result, number, int(time.time()) - self.init_time))

    @chainable
    def on_run(self):

        # Register start time
        self.init_time = int(time.time())

        # Run a few numbers through the roundrobin endpoint.
        # These are async calls, we process the results in a separate 'callback'
        # function.
        # - Use 'parallel' endpoint to speed things up by round robin load
        #   balancing over multiple instances of the roundrobin microservice.
        # - Use 'sequential' endpoint to run the code sequential.
        for number in range(4):
            response = self.call('mdgroup.roundrobin.endpoint.sequential', {"number": number})
            response.addCallback(self.append, number)


if __name__ == '__main__':
    main(UserSession)
