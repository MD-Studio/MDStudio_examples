# -*- coding: utf-8 -*-

import os

from autobahn.twisted.util import sleep

from mdstudio.deferred.chainable import chainable
from mdstudio.component.session import ComponentSession
from mdstudio.runner import main

from mdstudio_workflow import Workflow

CURRDIR = os.getcwd()


class LoopDemonstrationWorkflow(ComponentSession):
    """
    Workflow for demonstrating the use of looping constructs in a MDStudio
    workflow with the help of a 'LoopTask'
    """

    def authorize_request(self, uri, claims):
        return True

    @chainable
    def on_run(self):

        # Build Workflow
        wf = Workflow(project_dir='./loop_workflow')
        wf.task_runner = self

        # Task 1: Task that will provide an array of values that will be
        #         iterated over. Setting output_format=mol2 directly as input
        #         to this task is to demonstrate that parameters passed to the
        #         LoopTask will be forwarded to the mapped workflows created by
        #         the LoopTask. Equally so for steps=100 illustrating that input
        #         of steps in the workflow can obtained from tasks outside of
        #         the loop
        t1 = wf.add_task('Array provider')
        t1.set_input(output_format='mol2',
                     steps=100)

        # Task 2: Add loop task. The 'mapper_arg' defines the parameter name in
        #         the input that holds an iterable of input values to iterate
        #         over. The 'loop_end_task' is required and defines the task
        #         that 'closes' the loop and collects all results.
        t2 = wf.add_task('Loop',
                         task_type='LoopTask',
                         mapper_arg='smiles',
                         loop_end_task='Collector')
        wf.connect_task(t1.nid, t2.nid)

        # Task 3: Convert SMILES to mol2
        # Convert ligand to mol2 format irrespective of input format.
        t3 = wf.add_task('Ligand conversion',
                         task_type='WampTask',
                         uri='mdgroup.mdstudio_structures.endpoint.convert')
        wf.connect_task(t2.nid, t3.nid, smiles='mol')

        # Task 4: Convert mol2 to 3D mol2 irrespective if input is 1D/2D or 3D
        #         mol2 If 'output_format' is not specified it is deduced from
        #         the input wich is mol2 in this case. There are circumstances
        #         where conversion to 3D fails, retry upto 3 times.
        t4 = wf.add_task('Make_3D',
                         task_type='WampTask',
                         uri='mdgroup.mdstudio_structures.endpoint.make3d',
                         retry_count=3)
        wf.connect_task(t3.nid, t4.nid, 'mol')
        wf.connect_task(t1.nid, t4.nid, 'steps')

        # Task 5: Empty task that server as a collector for all results
        #         obtained during iteration.
        t5 = wf.add_task('Collector')
        wf.connect_task(t4.nid, t5.nid, 'mol')

        # Set the array of input SMILES string to task 1
        wf.input(t1.nid, smiles=['O1[C@@H](CCC1=O)CCC',
                                 'C[C@]12CC[C@H]3[C@@H](CC=C4CCCC[C@]34CO)[C@@H]1CCC2=O',
                                 'CC12CCC3C(CC=C4C=CCCC34C)C1CCC2=O'])

        wf.run()
        while wf.is_running:
            yield sleep(1)


if __name__ == "__main__":
    main(LoopDemonstrationWorkflow, auto_reconnect=False, daily_log=False)
