from __future__ import print_function

import time

from openmdao.components.execcomp import ExecComp

class ExecComp4Test(ExecComp):
    """
    A version of ExecComp for benchmarking.
    """
    def __init__(self, exprs, nl_delay=0.01, lin_delay=0.01,
                 **kwargs):
        super(ExecComp4Test, self).__init__(exprs, **kwargs)
        self.nl_delay = nl_delay
        self.lin_delay = lin_delay

    def solve_nonlinear(self, params, unknowns, resids):
        super(ExecComp4Test, self).solve_nonlinear(params, unknowns, resids)
        time.sleep(self.nl_delay)

    def apply_linear(self, params, unknowns, dparams, dunknowns, dresids, mode):
        self._apply_linear_jac(params, unknowns, dparams, dunknowns, dresids, mode)
        time.sleep(self.lin_delay)
