# Load balancing microservices

Microservices are independently running entities registering endpoints with the MDStudio broker.

These endpoints should be unique by default but MDStudio allows you to use load balancing
endpoint registration options to register multiple of the same endpoints offered through multiple
instances of the same microservice.

This is a convenient way to scale-up calculations by launching multiple instances of the same
microservice on dedicated hardware, possibly distributed.
The power of this approach become even more pronounced when a microservice is offered as a docker
container and they are orchestrated using [kubernetes](https://kubernetes.io) for instance.


## Using round-robin load balancing in a microservice

The `roundrobin` example illustrates the use of round-robin endpoint registration option as a
way to perform load balancing. It is a simple Python microservice build using the MDStudio
framework explained in the `hello_world` example. 

As you go through the code you will quickly see that the only requirements for using round-robin
registration is in `application.py`:

    from autobahn.wamp import RegisterOptions
    
and in the endpoint registration:

    @endpoint('parallel', 'roundrobin-request', 'roundrobin-response',
              options=RegisterOptions(invoke=u'roundrobin'))

That's it!

## Using the roundrobin microservice

The `roundrobin` microservice exposes two endpoints:

- `parallel` uses the roundrobin registration option
- `sequential` uses default registration

Now open some terminal windows and launch two or three of the `roundrobin` microservices
and execute the `call_endpoint.py` script.
This script will call the `parallel` or `sequential` endpoint with a series of input numbers
and report the time it takes to finish all of the calls. This should be substantially faster 
using round-robin load balancing depending on the number of microservices launched in parallel
and the CPU resources you have available.
