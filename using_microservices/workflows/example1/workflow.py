# -*- coding: utf-8 -*-

import os

from autobahn.twisted.util import sleep

from mdstudio.deferred.chainable import chainable
from mdstudio.component.session import ComponentSession
from mdstudio.runner import main

from mdstudio_workflow import Workflow


class ExampleWorkflow(ComponentSession):
    """
    Workflow manager example workflow

    This simple workflow performs a series of structure conversion steps going
    from a ligand SMILES sting to a 3D structure with correct protonation state.
    Subsequently it docks the ligand in the active site of a protein using the
    PLANTS docking software, performs a clustering of the results and selects
    cluster medians.

    This example illustrates how to:
    * Build a workflow specification by connecting together a number of tasks.
    * Use both 'WampTask' and 'PythonTask' types to respectively combine
      microservice endpoint methods with (custom) python functions in the same
      workflow.
    * Save the constructed workflow as a specification that can be reused
      with different input.
    * Run the specifications for a few different ligands in sequence.
    * See how the workflow manager collects all task input and output locally
      in a structures project directory.
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

        # Workflow constants, these will be saved as part of the workflow
        # specification
        ligand_format = 'smi'
        pH = 7.4
        protein_file = os.path.abspath('protein.mol2')
        protein_binding_center = [4.9264, 19.0796, 21.9892]

        # Build Workflow
        wf = Workflow(description='MDStudio WAMP workflow')

        # Task 1: convert the SMILES string to mol2 format (2D).
        # Add a task using the 'add_task' method always defining:
        # an administrative title of the task and the task type here a WampTask
        # because we are calling an microservice endpoint defined by uri.
        # 'store_output' is True by default and stores the task input/output to disk.
        t1 = wf.add_task('Format_conversion',
                         task_type='WampTask',
                         uri='mdgroup.mdstudio_structures.endpoint.convert')

        # Use 'set_input' do define the input to a task. As we are now building
        # a workflow specification these will be task constants but the same
        # method will be used later on to define specific input when using the
        # workflow specification for a ligand.
        t1.set_input(output_format='mol2')

        # Task 2: Covert mol2 to 3D mol2 irrespective if input is 1D/2D or 3D mol2
        # This particular 3D conversion routine is known to fail sometimes but by
        # setting retry_count to 3 the workflow manager will retry 3 times before
        # failing.
        t2 = wf.add_task('Make_3D',
                         task_type='WampTask',
                         uri='mdgroup.mdstudio_structures.endpoint.make3d',
                         retry_count=3)
        t2.set_input(output_format='mol2')

        # Use 'connect_task' to connect t1 to t2 using their unique identifiers
        # (nid). In addition we can specify the parameters for task 1 we wish to
        # use as input to task 2 as additional argument or keyword arguments to
        # the functions. A keyword argument defines a parameter name mapping
        # between the two tasks.
        wf.connect_task(t1.nid, t2.nid, 'mol')

        # Task 3: Adjust ligand protonation state to a given pH if applicable
        t3 = wf.add_task('Add hydrogens',
                         task_type='WampTask',
                         uri='mdgroup.mdstudio_structures.endpoint.addh')
        t3.set_input(output_format='mol2',
                     correctForPH=True,
                     pH=pH)
        wf.connect_task(t2.nid, t3.nid, 'mol')

        # Task 4: Get the formal charge for the protonated mol2 to use as input
        # for ACPYPE or ATB
        # Here store_output equals False which will keep all output in memory and
        # finally as part of the stored workflow file (*.jgf)
        t4 = wf.add_task('Get charge',
                         task_type='WampTask',
                         uri='mdgroup.mdstudio_structures.endpoint.info',
                         store_output=False)
        t4.set_input(input_format='mol2')
        wf.connect_task(t3.nid, t4.nid, 'mol')

        # Task 5: Create rotations of the molecule for better sampling
        t5 = wf.add_task('Create 3D rotations',
                         task_type='WampTask',
                         uri='mdgroup.mdstudio_structures.endpoint.rotate')
        t5.set_input(rotations=[[1, 0, 0, 90], [1, 0, 0, -90], [0, 1, 0, 90], [0, 1, 0, -90], [0, 0, 1, 90],
                                [0, 0, 1, -90]])
        wf.connect_task(t3.nid, t5.nid, 'mol')

        # Task 6: Run PLANTS on ligand and protein
        # The 'workdir' argument points to a tmp directory that is shared between
        # the microservice docker image and the host system to store results.
        t6 = wf.add_task('Plants docking',
                         task_type='WampTask',
                         uri='mdgroup.mdstudio_smartcyp.endpoint.docking')
        t6.set_input(cluster_structures=100,
                     bindingsite_center=protein_binding_center,
                     bindingsite_radius=12,
                     protein_file=protein_file,
                     threshold=3.0,
                     base_work_dir='/tmp/mdstudio/mdstudio_smartcyp')

        # Here we pass only the 'mol' parameter from task 5 to task 6 where it is
        # named 'ligand_file'
        wf.connect_task(t5.nid, t6.nid, 'mol', mol='ligand_file')

        # Task 7: Extract cluster medians from output using a custom function.

        # A task of type 'PythonTask' allows to add custom python functions
        # or classes to the workflow. They are defined using the 'custom_func'
        # parameter according to the Python import syntax. The package or file
        # containing the function should be available as part of the PYTHONPATH.
        t7 = wf.add_task('Get cluster medians',
                         task_type='PythonTask',
                         custom_func='workflow_helpers.get_docking_medians')
        wf.connect_task(t6.nid, t7.nid, 'result')

        # Task 8: retrieve median structures
        t8 = wf.add_task('Retrieve median structures',
                         task_type='WampTask',
                         uri='mdgroup.mdstudio_smartcyp.endpoint.docking_structures')
        t8.set_input(create_ensemble=False)
        wf.connect_task(t7.nid, t8.nid, medians='paths')

        # Save the workflow specification
        wf.save('workflow_spec.jgf')

        # Lets run the workflow specification for a number of ligand SMILES
        # The current microservice instance (self) is passed as task_runner to the workflow
        # it will be used to make calls to other microservice endpoints when task_type equals WampTask.
        wf.task_runner = self

        currdir = os.getcwd()
        for i, ligand in enumerate(['O1[C@@H](CCC1=O)CCC',
                                    'C[C@]12CC[C@H]3[C@@H](CC=C4CCCC[C@]34CO)[C@@H]1CCC2=O',
                                    'CC12CCC3C(CC=C4C=CCCC34C)C1CCC2=O'], start=1):
            wf.load('workflow_spec.jgf')
            wf.input(t1.nid, mol={'content': ligand, 'path': None, 'extension': ligand_format})
            wf.run(project_dir='./ligand-{0}'.format(i))
            while wf.is_running:
                yield sleep(1)

            os.chdir(currdir)


if __name__ == "__main__":
    main(ExampleWorkflow, auto_reconnect=False, daily_log=False)
