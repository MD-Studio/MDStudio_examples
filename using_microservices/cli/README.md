# Command Line Interface to MDStudio microservices

MDStudio offers a simple command line interface (CLI) to interact with microservice endpoints
in the running MDStudio environment.

The CLI, called `mdstudio-cli` itself is a Python microservice available from [GitHub](https://github.com/MD-Studio/MDStudio_cli).
After installation it is available as command line tool.

> **NOTE:** ensure you have a `settings.yml` file with your MDStudio authentication and authorization credentials 
  available in the directory where you launch `mdstudio-cli`. a functional example environment is provided for the CLI
  demonstration cases. 

## Using mdstudio-cli to communicate with the Python example microservice build previously

Sending a 'greeting' message to the example 'Hello world' microservice:

    >>> mdstudio-cli -u mdgroup.hello_world.endpoint.hello --greeting 'Hello from CLI'

Omitting the 'greeting' parameter fails as it is set as 'required' in the JSON schema of the 'hello' endpoint

    >>> mdstudio-cli -u mdgroup.hello_world.endpoint.hello
    
## Some other examples with various MDStudio microservices

Using the lie_structures microservice to convert a molecule structure file format from 'mol2' to 'pdb'

    >>> mdstudio-cli -u mdgroup.mdstudio_structures.endpoint.convert --mol asperine.mol2 --output_format pdb

List available cheminformatics packages offered by the lie_structures service

    >>> mdstudio-cli -u mdgroup.mdstudio_structures.endpoint.supported_toolkits

Get some information on a molecular structure

    >>> mdstudio-cli -u mdgroup.mdstudio_structures.endpoint.info --mol asperine.mol2 --input_format mol2

Query for topology and parameter files in [Automated Topology Builder](https://atb.uq.edu.au) database based on a compound common name

    >>> mdstudio-cli -u mdgroup.mdstudio_atb.endpoint.molecule_query --common_name aspirin --atb_api_token <ATB API token>

Using SMARTCyp for a Site-Of-Metabolism (SOM) prediction for aspirin.

    >>> mdstudio-cli -u mdgroup.mdstudio_smartcyp.endpoint.smartcyp --ligand_file aspirin.mol2

