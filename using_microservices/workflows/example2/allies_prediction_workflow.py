# -*- coding: utf-8 -*-

import os
import glob
import pickle

from autobahn.twisted.util import sleep

from mdstudio.deferred.chainable import chainable
from mdstudio.component.session import ComponentSession
from mdstudio.runner import main

from lie_workflow import Workflow

CURRDIR = os.getcwd()


class LIEPredictionWorkflow(ComponentSession):
    """
    This workflow will perform a binding affinity prediction for CYP 1A2 with
    applicability domain analysis using the Linear Interaction Energy (LIE)
    method as described in:

    Capoferri L, Verkade-Vreeker MCA, Buitenhuis D, Commandeur JNM, Pastor M,
    Vermeulen NPE, et al. (2015) "Linear Interaction Energy Based Prediction
    of Cytochrome P450 1A2 Binding Affinities with Reliability Estimation."
    PLoS ONE 10(11): e0142232. https://doi.org/10.1371/journal.pone.0142232

    The workflow uses data from the pre-calibrated CYP1A2 model created using
    the eTOX ALLIES Linear Interaction Energy pipeline (liemodel parameter).
    Pre-calculated molecular dynamics trajectory LIE energy values are
    available for bound and unbound ligand cases (bound_trajectory,
    unbound_trajectory respectively)
    """

    def authorize_request(self, uri, claims):
        return True

    @chainable
    def on_run(self):
        
        # Workflow input data. Would normally be obtained from other LIE
        # workflow that runs docking and MD.
        ligand = 'O1[C@@H](CCC1=O)CCC'
        ligand_format = 'smi'
        unbound_trajectory = os.path.join(CURRDIR, "mddata-0-0.ene")
        bound_trajectory = [os.path.join(CURRDIR, ene) for ene in glob.glob('mddata-1*.ene')]
        decompose_files = [os.path.join(CURRDIR, ene) for ene in glob.glob('mddata-1*.decomp')]

        # Static input data: CYP1A2 pre-calibrated model
        modelpicklefile = os.path.join(CURRDIR, '1A2_model.pkl')
        modelfile = pickle.load(open(modelpicklefile))
        

        # Build Workflow
        wf = Workflow(project_dir='./lie_prediction')
        wf.task_runner = self

        # STAGE 5. PYLIE FILTERING, AD ANALYSIS AND BINDING-AFFINITY PREDICTION
        # Collect Gromacs bound and unbound MD energy trajectories in a dataframe
        t18 = wf.add_task('Create mdframe',
                          task_type='WampTask', 
                          uri='mdgroup.lie_pylie.endpoint.collect_energy_trajectories')
        t18.set_input(unbound_trajectory=unbound_trajectory,
                      bound_trajectory=bound_trajectory)
        
        # Determine stable regions in MDFrame and filter
        t19 = wf.add_task('Detect stable regions',
                          task_type='WampTask',
                          uri='mdgroup.lie_pylie.endpoint.filter_stable_trajectory')
        t19.set_input(do_plot=True,
                      workdir='/tmp/mdstudio/lie_pylie')
        wf.connect_task(t18.nid, t19.nid, 'mdframe')
     
        # Extract average LIE energy values from the trajectory
        t20 = wf.add_task('LIE averages',
                          task_type='WampTask',
                          uri='mdgroup.lie_pylie.endpoint.calculate_lie_average')
        wf.connect_task(t19.nid, t20.nid, 'filtered_mdframe', filtered_mdframe='mdframe')

        # Calculate dG using pre-calibrated model parameters
        t21 = wf.add_task('Calc dG',
                          task_type='WampTask',
                          uri='mdgroup.lie_pylie.endpoint.liedeltag')
        t21.set_input(alpha_beta_gamma=modelfile['LIE']['params'])
        wf.connect_task(t20.nid, t21.nid, 'averaged', averaged='dataframe')

        # Applicability domain: 1. Tanimoto similarity with training set
        t22 = wf.add_task('AD1 tanimoto simmilarity',
                          task_type='WampTask',
                          uri='mdgroup.lie_structures.endpoint.chemical_similarity')
        t22.set_input(test_set=[ligand],
                      reference_set=modelfile['AD']['Tanimoto']['smi'],
                      ci_cutoff=modelfile['AD']['Tanimoto']['Furthest'])
        wf.connect_task(t18.nid, t22.nid)

        # Applicability domain: 2. residue decomposition
        t23 = wf.add_task('AD2 residue decomposition',
                          task_type='WampTask',
                          uri='mdgroup.lie_pylie.endpoint.adan_residue_decomp',
                          inline_files=False)
        t23.set_input(model_pkl=modelpicklefile,
                      decompose_files=decompose_files)
        wf.connect_task(t18.nid, t23.nid)

        # Applicability domain: 3. deltaG energy range
        t24 = wf.add_task('AD3 dene yrange',
                          task_type='WampTask',
                          uri='mdgroup.lie_pylie.endpoint.adan_dene_yrange')
        t24.set_input(ymin=modelfile['AD']['Yrange']['min'],
                      ymax=modelfile['AD']['Yrange']['max'])
        wf.connect_task(t21.nid, t24.nid, 'liedeltag_file', liedeltag_file='dataframe')

        # Applicability domain: 4. deltaG energy distribution
        t25 = wf.add_task('AD4 dene distribution',
                          task_type='WampTask',
                          uri='mdgroup.lie_pylie.endpoint.adan_dene')
        t25.set_input(model_pkl=modelpicklefile,
                      center=list(modelfile['AD']['Dene']['Xmean']),
                      ci_cutoff=modelfile['AD']['Dene']['Maxdist'])
        wf.connect_task(t21.nid, t25.nid, 'liedeltag_file', liedeltag_file='dataframe')

        wf.run()
        while wf.is_running:
            yield sleep(1)


if __name__ == "__main__":
    main(LIEPredictionWorkflow)