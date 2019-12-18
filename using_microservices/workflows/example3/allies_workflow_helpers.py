# -*- coding: utf-8 -*-

"""
file: allies_workflow_helpers.py

Helper Python functions used in the allies workflow.
"""


def get_docking_medians(**kwargs):
    """
    Get median docking solutions after clustering of docking poses.
    For now return only one solution until the workflow engine can handle multiple
    solutions transparently in a flow based manner.

    :param kwargs:
    :return:
    """

    medians = [v.get('PATH') for v in kwargs.get('result', {}).values() if v.get('MEAN', True)]

    return {'medians': medians}


def collect_md_enefiles(bound=None, unbound=None, **kwargs):

    # Get the output from the MD microservice
    output = {'unbound_trajectory': unbound['results']['energy_dataframe']}

    if isinstance(bound, dict):
        output['bound_trajectory'] = [bound['results']['energy_dataframe']]
        output['decomp_files'] = [bound['results']['decompose_dataframe']]
    elif isinstance(bound, list):
        output['bound_trajectory'] = [b['results']['energy_dataframe'] for b in bound]
        output['decomp_files'] = [b['results']['decompose_dataframe']for b in bound]

    return output
