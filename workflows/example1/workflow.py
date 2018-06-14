# -*- coding: utf-8 -*-

from autobahn.twisted.util import sleep

from mdstudio.deferred.chainable import chainable
from mdstudio.component.session import ComponentSession
from mdstudio.runner import main

from lie_workflow import Workflow


class ExampleWorkflow(ComponentSession):
    """
    Example workflow demonstrating some of the capabilities of microservices
    and the microservice oriented workflow manager.

    It performs a series of structure conversion steps going from a ligand
    SMILES sting to a 3D structure with correct protonation state.
    Subsequently it docks the ligand in the active site of a protein, performs
    a clustering of the results and selects cluster medians.
    """

    def authorize_request(self, uri, claims):
        """
        Microservice specific authorization method.

        Will always be called when the service first tries to register with the
        broker. It returns True (= authorized) by default.
        """
        return True

    @chainable
    def on_run(self):
        """
        When the microservice has successfully registered with the broker the
        on_run method is the first method to be called.
        We are using this method now to run our example workflow.
        """

        # Workflow constants
        ligands = ['O1[C@@H](CCC1=O)CCC',
                   'C[C@]12CC[C@H]3[C@@H](CC=C4CCCC[C@]34CO)[C@@H]1CCC2=O',
                   'CC12CCC3C(CC=C4C=CCCC34C)C1CCC2=O']
        ligand_format = 'smi'
        pH=7.4
        protein_file = '/Users/mvdijk/Documents/WorkProjects/liestudio-master/MDStudio/scripts/1A2_model/DT_conf_1.mol2'
        protein_binding_center = [4.9264, 19.0796, 21.9892]

        # Build Workflow
        wf = Workflow()

        # The current microservice instance (self) is passed as task_runner to the workflow
        # it will be used to make calls to other microservice endpoints when task_type equals WampTask.
        wf.task_runner = self

        for ligand in ligands:

            # convert the SMILES string to mol2 format (2D). Store output to file
            t1 = wf.add_task('Format_conversion', task_type='WampTask', uri='mdgroup.lie_structures.endpoint.convert',
                             store_output=True)
            t1.set_input(input_format=ligand_format, output_format='mol2', mol=ligand, from_file=False,
                         workdir='/tmp/mdstudio/lie_structures')

            if wf.workflow.root != t1.nid:
                wf.connect_task(wf.workflow.root, t1.nid)

            # Covert mol2 to 3D mol2 irrespective if input is 1D/2D or 3D mol2
            t2 = wf.add_task('Make_3D', task_type='WampTask', uri='mdgroup.lie_structures.endpoint.make3d',
                             store_output=True, retry_count=3)
            t2.set_input(input_format='mol2', output_format='mol2', from_file=False, to_file=False)
            wf.connect_task(t1.nid, t2.nid, 'mol')

            # Adjust ligand protonation state to a given pH if applicable
            t3 = wf.add_task('Add hydrogens', task_type='WampTask', uri='mdgroup.lie_structures.endpoint.addh',
                             store_output=True)
            t3.set_input(input_format='mol2', output_format='mol2', correctForPH=True, pH=pH, from_file=False, to_file=False)
            wf.connect_task(t2.nid, t3.nid, 'mol')

            # Get the formal charge for the protonated mol2 to use as input for ACPYPE or ATB
            t4 = wf.add_task('Get charge', task_type='WampTask', uri='mdgroup.lie_structures.endpoint.info')
            t4.set_input(input_format='mol2', output_format='mol2', from_file=False, to_file=False)
            wf.connect_task(t3.nid, t4.nid, 'mol')

            # Create rotations of the molecule for better sampling
            t6 = wf.add_task('Create 3D rotations', task_type='WampTask', uri='mdgroup.lie_structures.endpoint.rotate',
                             store_output=True)
            t6.set_input(input_format='mol2', from_file=False, to_file=False,
                         rotations=[[1, 0, 0, 90], [1, 0, 0, -90], [0, 1, 0, 90], [0, 1, 0, -90], [0, 0, 1, 90],
                                    [0, 0, 1, -90]],
                         workdir='/tmp/mdstudio/lie_structures')
            wf.connect_task(t3.nid, t6.nid, 'mol')

            # Run PLANTS on ligand and protein
            t7 = wf.add_task('Plants docking', task_type='WampTask', uri='mdgroup.lie_plants_docking.endpoint.docking',
                             store_output=True)
            t7.set_input(cluster_structures=100,
                         bindingsite_center=protein_binding_center,
                         bindingsite_radius=12,
                         protein_file=protein_file,
                         min_rmsd_tolerance=3.0,
                         exec_path='/tmp/mdstudio/lie_plants_docking/plants_linux',
                         workdir='/tmp/mdstudio/lie_plants_docking')
            wf.connect_task(t6.nid, t7.nid, mol='ligand_file')

        # Save the workflow specification
        wf.save('workflow_spec.jgf')

        wf.run()
        while wf.is_running:
            yield sleep(1)




if __name__ == "__main__":
    main(ExampleWorkflow)