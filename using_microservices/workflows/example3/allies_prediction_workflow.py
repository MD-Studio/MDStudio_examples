# -*- coding: utf-8 -*-

import os
import pickle

from autobahn.twisted.util import sleep

from mdstudio.deferred.chainable import chainable
from mdstudio.component.session import ComponentSession
from mdstudio.runner import main

from mdstudio_workflow import Workflow


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

        # CYP1A2 pre-calibrated model
        modelpicklefile = os.path.join(liemodel, 'params.pkl')
        modelfile = pickle.load(open(modelpicklefile))
        unbound_trajectory = os.path.join(os.getcwd(), "unbound_trajectory.ene")
        bound_trajectory = [os.path.join(os.getcwd(), "bound_trajectory.ene")]
        decompose_files = [os.path.join(os.getcwd(), "decompose_dataframe.ene")]

        # Build Workflow
        wf = Workflow(project_dir='./lie_prediction')
        wf.task_runner = self

        # STAGE 5. PYLIE FILTERING, AD ANALYSIS AND BINDING-AFFINITY PREDICTION
        # Collect Gromacs bound and unbound MD energy trajectories in a dataframe
        t18 = wf.add_task('Create mdframe',
                          task_type='WampTask',
                          uri='mdgroup.lie_pylie.endpoint.collect_energy_trajectories')
        t18.set_input(unbound_trajectory=unbound_trajectory,
                      bound_trajectory=bound_trajectory,
                      lie_vdw_header="Ligand-Ligenv-vdw",
                      lie_ele_header="Ligand-Ligenv-ele")

        # Determine stable regions in MDFrame and filter
        t19 = wf.add_task('Detect stable regions',
                          task_type='WampTask',
                          uri='mdgroup.lie_pylie.endpoint.filter_stable_trajectory')
        t19.set_input(do_plot=True,
                      minlength=45,
                      workdir='/tmp/mdstudio/lie_pylie')
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
        t21.set_input(alpha_beta_gamma=modelfile['LIE']['params'])
        wf.connect_task(t20.nid, t21.nid, 'averaged', averaged='dataframe')

        # Applicability domain: 1. Tanimoto similarity with training set
        t22 = wf.add_task('AD1 tanimoto simmilarity',
                          task_type='WampTask',
                          uri='mdgroup.mdstudio_structures.endpoint.chemical_similarity')
        t22.set_input(test_set=[ligand], mol_format=ligand_format, reference_set=modelfile['AD']['Tanimoto']['smi'],
                      ci_cutoff=modelfile['AD']['Tanimoto']['Furthest'])
        wf.connect_task(t18.nid, t22.nid)

        # Applicability domain: 2. residue decomposition
        t23 = wf.add_task('AD2 residue decomposition',
                          task_type='WampTask',
                          uri='mdgroup.lie_pylie.endpoint.adan_residue_decomp',
                          inline_files=False)
        t23.set_input(model_pkl=modelpicklefile, decompose_files=decompose_files)
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
    main(LIEPredictionWorkflow, auto_reconnect=False, daily_log=False)
