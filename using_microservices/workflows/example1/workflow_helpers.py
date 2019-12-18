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

    medians = [v.get('PATH') for v in kwargs.get('result', {}).values() if v.get('MEAN', True)]

    return {'medians': medians}
