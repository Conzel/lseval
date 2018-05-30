# -*- coding: utf-8 -*-
"""
Functionset for flexible cumulant fitting.
"""


def cumulantFunction(numCumulants):
    """
    Produces cumulant function (returns lambda) that contains as many cumulants
    as specified by numCumulants.

    Input:
        numCumulants: Number of cumulants that should be included in the
        function.
    Output:
        lambda function according to multi-cumulant fitting model
        (ln[g1(tau)]) = ln B - Gamma*tau + mu2*tau**2/2
        numCumulants = 1 returns single exponential fit.
    """
    # TODO: Add the lambda output of the function, push to github

    # for k in numCumulants:
    #     if k == 1:
    #         lambda x: 1
    #     else:
    #         lambda y, a:
    if numCumulants == 1:
        return
    else:
        if numCumulants % 2 == 0
            lambda mu, tau: -
