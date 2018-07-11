# -*- coding: utf-8 -*-

"""
file: workflow_helpers.py

Helper Python functions used in the example1 workflow.
"""


def get_docking_medians(**kwargs):
    """
    Get median docking solutions after clustering of docking poses.
    For now return only one solution until the workflow engine can handle multiple
    solutions transparently in a flow based manner.

    :param kwargs:
    :return:
    """

    medians = [v.get('path') for v in kwargs.get('output', {}).values() if v.get('mean', True)]
    if medians:
        return {'medians': medians[0]}
