""" Test out some crucial linear GS tests in parallel."""

from __future__ import print_function

from openmdao.core.mpiwrap import MPI, MultiProcFailCheck
from openmdao.core.parallelgroup import ParallelGroup
from openmdao.core.problem import Problem
from openmdao.solvers.ln_gauss_seidel import LinearGaussSeidel
from openmdao.test.mpiunittest import MPITestCase
from openmdao.test.simplecomps import FanOutGrouped, FanInGrouped
from openmdao.core.mpiwrap import MPI, MultiProcFailCheck
from openmdao.test.testutil import assert_rel_error

if MPI:
    from openmdao.core.petscimpl import PetscImpl as impl
else:
    from openmdao.core.basicimpl import BasicImpl as impl


class MPITests1(MPITestCase):

    N_PROCS = 2

    def test_fan_out_grouped(self):

        prob = Problem(impl=impl)
        prob.root = FanOutGrouped()
        prob.root.ln_solver = LinearGaussSeidel()
        prob.root.sub.ln_solver = LinearGaussSeidel()
        prob.setup(check=False)
        prob.run()

        param_list = ['p.x']
        #unknown_list = ['sub.comp2.y', "sub.comp3.y"]
        unknown_list = ['c2.y', "c3.y"]

        J = prob.calc_gradient(param_list, unknown_list, mode='fwd', return_format='dict')
        #assert_rel_error(self, J['sub.comp2.y']['p.x'][0][0], -6.0, 1e-6)
        #assert_rel_error(self, J['sub.comp3.y']['p.x'][0][0], 15.0, 1e-6)
        assert_rel_error(self, J['c2.y']['p.x'][0][0], -6.0, 1e-6)
        assert_rel_error(self, J['c3.y']['p.x'][0][0], 15.0, 1e-6)

        J = prob.calc_gradient(param_list, unknown_list, mode='rev', return_format='dict')
        #assert_rel_error(self, J['sub.comp2.y']['p.x'][0][0], -6.0, 1e-6)
        #assert_rel_error(self, J['sub.comp3.y']['p.x'][0][0], 15.0, 1e-6)
        assert_rel_error(self, J['c2.y']['p.x'][0][0], -6.0, 1e-6)
        assert_rel_error(self, J['c3.y']['p.x'][0][0], 15.0, 1e-6)

    def test_fan_in_grouped(self):

        prob = Problem(impl=impl)
        prob.root = FanInGrouped()
        prob.root.ln_solver = LinearGaussSeidel()
        prob.root.sub.ln_solver = LinearGaussSeidel()
        prob.setup(check=False)
        prob.run()

        param_list = ['p1.x1', 'p2.x2']
        unknown_list = ['comp3.y']

        J = prob.calc_gradient(param_list, unknown_list, mode='fwd', return_format='dict')
        assert_rel_error(self, J['comp3.y']['p1.x1'][0][0], -6.0, 1e-6)
        assert_rel_error(self, J['comp3.y']['p2.x2'][0][0], 35.0, 1e-6)

        J = prob.calc_gradient(param_list, unknown_list, mode='rev', return_format='dict')
        assert_rel_error(self, J['comp3.y']['p1.x1'][0][0], -6.0, 1e-6)
        assert_rel_error(self, J['comp3.y']['p2.x2'][0][0], 35.0, 1e-6)

if __name__ == '__main__':
    from openmdao.test.mpiunittest import mpirun_tests
    mpirun_tests()
