# Command Line Interface to MDStudio microservices

MDStudio offers a simple command line interface (CLI) to interact with microservice endpoints
in the running MDStudio environment.

The CLI, called `lie_cli` itself is a Python microservice available from [GitHub](https://github.com/MD-Studio/lie_cli).
You can install and run it as described in README file in ~/building_microservices/Python/ directory
of this repository.

## Some examples using lie_cli

Sending a 'greeting' message to the example 'Hello world' microservice:

    >>> python -m lie_cli -u mdgroup.hello_world.endpoint.hello --greeting 'Hello from CLI'

Omitting the 'greeting' parameter fails as it is set as 'required' in the JSON schema of the 'hello' endpoint

    >>> python -m lie_cli -u mdgroup.hello_world.endpoint.hello

Using the lie_structures microservice to convert a molecule structure file format from 'mol2' to 'pdb'

    >>> python -m lie_cli -u mdgroup.lie_structures.endpoint.convert --mol asperine.mol2 --output_format pdb --input_format mol2

List available cheminformatics packages offerd by the lie_structures service

    >>> python -m lie_cli -u mdgroup.lie_structures.endpoint.supported_toolkits

Query for topology and parameter files in [Automated Topology Builder](https://atb.uq.edu.au) database based on a compound common name

    >>> python -m lie_cli -u mdgroup.lie_atb.endpoint.molecule_query --common_name aspirin --atb_api_token <ATB API token>
