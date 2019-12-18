# -*- coding: utf-8 -*-

import os
import pickle
import json

from autobahn.twisted.util import sleep

from mdstudio.deferred.chainable import chainable
from mdstudio.component.session import ComponentSession
from mdstudio.runner import main

from mdstudio_workflow import Workflow


class LIEWorkflow(ComponentSession):
    """
    This workflow will perform a binding affinity prediction for CYP 1A2 with
    applicability domain analysis using the Linear Interaction Energy (LIE)
    method as described in:

    Capoferri L, Verkade-Vreeker MCA, Buitenhuis D, Commandeur JNM, Pastor M,
    Vermeulen NPE, et al. (2015) "Linear Interaction Energy Based Prediction
    of Cytochrome P450 1A2 Binding Affinities with Reliability Estimation."
    PLoS ONE 10(11): e0142232. https://doi.org/10.1371/journal.pone.0142232

    The workflow uses data from the pre-calibrated CYP1A2 model created using
    the eTOX ALLIES Linear Interaction Energy pipeline.
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

        # Ligand to make prediction for
        ligand = 'O1[C@@H](CCC1=O)CCC'
        ligand_format = 'smi'
        liemodel = os.path.join(os.getcwd(), '1A2_model')

        # CYP1A2 Model data
        with open(os.path.join(liemodel, 'model.dat'), 'r') as mdf:
            model = json.load(mdf)

        # CYP1A2 pre-calibrated model
        modelpicklefile = os.path.join(liemodel, 'params.pkl')
        modelfile = pickle.load(open(modelpicklefile))

        # Build Workflow
        wf = Workflow(project_dir='./allies_run')
        wf.task_runner = self

        # STAGE 1: LIGAND PRE-PROCESSING
        # Convert ligand to mol2 irrespective of input format.
        t1 = wf.add_task('Format_conversion',
                         task_type='WampTask',
                         uri='mdgroup.mdstudio_structures.endpoint.convert')
        t1.set_input(mol={'content': ligand, 'path': None, 'extension': ligand_format})

        # Covert mol2 to 3D mol2 irrespective if input is 1D/2D or 3D mol2
        t2 = wf.add_task('Make_3D',
                         task_type='WampTask',
                         uri='mdgroup.mdstudio_structures.endpoint.make3d')
        t2.set_input(output_format='mol2')
        wf.connect_task(t1.nid, t2.nid, 'mol')

        # Adjust ligand protonation state to a given pH if applicable
        t3 = wf.add_task('Add hydrogens',
                         task_type='WampTask',
                         uri='mdgroup.mdstudio_structures.endpoint.addh')
        t3.set_input(output_format='mol2',
                     correctForPH=model['pHCorr'],
                     pH=model['pH'])
        wf.connect_task(t2.nid, t3.nid, 'mol')

        # Get the formal charge for the protonated mol2 to use as input for ACPYPE or ATB
        t4 = wf.add_task('Get charge',
                         task_type='WampTask',
                         uri='mdgroup.mdstudio_structures.endpoint.info')
        t4.set_input(input_format='mol2')
        wf.connect_task(t3.nid, t4.nid, 'mol')


        # # STAGE 2. CREATE TOPOLOGY FOR LIGAND
        # Run acpype on ligands
        t5 = wf.add_task('ACPYPE',
                         task_type='WampTask',
                         uri='mdgroup.mdstudio_amber.endpoint.acpype',
                         retry_count=3)
        wf.connect_task(t3.nid, t5.nid, mol='structure')
        wf.connect_task(t4.nid, t5.nid, charge='net_charge')


        # STAGE 3. PLANTS DOCKING
        # Create rotations of the molecule for better sampling
        t6 = wf.add_task('Create 3D rotations',
                         task_type='WampTask',
                         uri='mdgroup.mdstudio_structures.endpoint.rotate')
        t6.set_input(rotations=[[1, 0, 0, 90], [1, 0, 0, -90], [0, 1, 0, 90], [0, 1, 0, -90], [0, 0, 1, 90],
                                [0, 0, 1, -90]])
        wf.connect_task(t3.nid, t6.nid, 'mol')

        # Run PLANTS on ligand and protein
        t7 = wf.add_task('Plants docking',
                         task_type='WampTask',
                         uri='mdgroup.mdstudio_smartcyp.endpoint.docking')
        t7.set_input(cluster_structures=100,
                     bindingsite_center=model['proteinParams'][0]['pocket'],
                     bindingsite_radius=model['proteinParams'][0]['radius'],
                     protein_file=os.path.join(liemodel, model['proteinParams'][0]['proteinDock']),
                     threshold=3.0,
                     base_work_dir='/tmp/mdstudio/mdstudio_smartcyp')
        wf.connect_task(t6.nid, t7.nid, mol='ligand_file')

        # Get cluster median structures from docking
        t8 = wf.add_task('Get cluster medians',
                         custom_func='allies_workflow_helpers.get_docking_medians')
        wf.connect_task(t7.nid, t8.nid, 'output')


        # STAGE 4. GROMACS MD
        # Ligand in solution
        t14 = wf.add_task('MD ligand in water',
                          task_type='WampTask',
                          uri='mdgroup.mdstudio_gromacs.endpoint.gromacs_ligand',
                          store_output=True)
        t14.set_input(sim_time=0.001, #sim_time=model['timeSim'],
                      include=[os.path.join(liemodel, model['proteinTopPos']), os.path.join(liemodel, 'attype.itp')],
                      residues=model['resSite'],
                      protein_file=None,
                      protein_top=os.path.join(liemodel, model['proteinTop']),
                      cerise_file=os.path.join(os.getcwd(), 'cerise_config_gt.json'))
        wf.connect_task(t5.nid, t14.nid, new_pdb='ligand_file', gmx_itp='topology_file')

        # convert PLANTS mol2 to pdb
        t15 = wf.add_task('Ligand mol2 to PDB',
                          task_type='WampTask',
                          uri='mdgroup.mdstudio_structures.endpoint.convert')
        t15.set_input(output_format='pdb')
        wf.connect_task(t8.nid, t15.nid, medians='mol')

        # Run MD for protein + ligand
        t16 = wf.add_task('MD protein-ligand',
                          task_type='WampTask',
                          uri='mdgroup.mdstudio_gromacs.endpoint.gromacs_protein')
        t16.set_input(sim_time=0.001,
                      include=[os.path.join(liemodel, model['proteinTopPos']), os.path.join(liemodel, 'attype.itp')],
                      residues=model['resSite'],
                      charge=model['charge'],
                      cerise_file=os.path.join(os.getcwd(), 'cerise_config_gt.json'),
                      protein_file=os.path.join(liemodel, model['proteinParams'][0]['proteinCoor']),
                      protein_top=os.path.join(liemodel, model['proteinTop']))
        wf.connect_task(t15.nid, t16.nid, mol='ligand_file')
        wf.connect_task(t5.nid, t16.nid, gmx_itp='topology_file')

        # Collect results
        t17 = wf.add_task('Collect MD results',
                          custom_func='allies_workflow_helpers.collect_md_enefiles')
        t17.set_input(model_dir=liemodel)
        wf.connect_task(t14.nid, t17.nid, output='unbound')
        wf.connect_task(t16.nid, t17.nid, output='bound')


        # STAGE 5. PYLIE FILTERING, AD ANALYSIS AND BINDING-AFFINITY PREDICTION
        # Collect Gromacs bound and unbound MD energy trajectories in a dataframe
        t18 = wf.add_task('Create mdframe',
                          task_type='WampTask',
                          uri='mdgroup.lie_pylie.endpoint.collect_energy_trajectories')
        t18.set_input(lie_vdw_header="Ligand-Ligenv-vdw", lie_ele_header="Ligand-Ligenv-ele")
        wf.connect_task(t17.nid, t18.nid, 'bound_trajectory', 'unbound_trajectory')

        # Determine stable regions in MDFrame and filter
        t19 = wf.add_task('Detect stable regions',
                          task_type='WampTask',
                          uri='mdgroup.lie_pylie.endpoint.filter_stable_trajectory')
        t19.set_input(do_plot=True, FilterSplines={'minlength': 45})
        wf.connect_task(t18.nid, t19.nid, 'mdframe')

        # Extract average LIE energy values from the trajectory
        t20 = wf.add_task('LIE averages',
                          task_type='WampTask',
                          uri='mdgroup.lie_pylie.endpoint.calculate_lie_average')
        wf.connect_task(t19.nid, t20.nid, filtered_mdframe='mdframe')

        # Calculate dG using pre-calibrated model parameters
        t21 = wf.add_task('Calc dG',
                          task_type='WampTask',
                          uri='mdgroup.lie_pylie.endpoint.liedeltag')
        t21.set_input(alpha=modelfile['LIE']['params'][0],
                      beta=modelfile['LIE']['params'][1],
                      gamma=modelfile['LIE']['params'][2])
        wf.connect_task(t20.nid, t21.nid, averaged='dataframe')

        # Applicability domain: 1. Tanimoto similarity with training set
        t22 = wf.add_task('AD1 tanimoto simmilarity',
                          task_type='WampTask',
                          uri='mdgroup.lie_structures.endpoint.chemical_similarity')
        t22.set_input(test_set=[ligand], mol_format=ligand_format, reference_set=modelfile['AD']['Tanimoto']['smi'],
                      ci_cutoff=modelfile['AD']['Tanimoto']['Furthest'])
        wf.connect_task(t18.nid, t22.nid)

        # Applicability domain: 2. residue decomposition
        t23 = wf.add_task('AD2 residue decomposition',
                          task_type='WampTask',
                          uri='mdgroup.lie_pylie.endpoint.adan_residue_decomp')
        t23.set_input(model_pkl=modelpicklefile)
        wf.connect_task(t17.nid, t23.nid, 'decomp_files')

        # Applicability domain: 3. deltaG energy range
        t24 = wf.add_task('AD3 dene yrange',
                          task_type='WampTask',
                          uri='mdgroup.lie_pylie.endpoint.adan_dene_yrange')
        t24.set_input(ymin=modelfile['AD']['Yrange']['min'], ymax=modelfile['AD']['Yrange']['max'])
        wf.connect_task(t21.nid, t24.nid, liedeltag_file='dataframe')

        # Applicability domain: 4. deltaG energy distribution
        t25 = wf.add_task('AD4 dene distribution',
                          task_type='WampTask',
                          uri='mdgroup.lie_pylie.endpoint.adan_dene')
        t25.set_input(model_pkl=modelpicklefile,
                      center=list(modelfile['AD']['Dene']['Xmean']),
                      ci_cutoff=modelfile['AD']['Dene']['Maxdist'])
        wf.connect_task(t21.nid, t25.nid, liedeltag_file='dataframe')

        # Save the workflow specification
        wf.save('workflow_spec.jgf')

        wf.run()
        while wf.is_running:
            yield sleep(1)


if __name__ == "__main__":
    main(LIEWorkflow, auto_reconnect=False, daily_log=False)
