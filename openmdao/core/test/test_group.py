
import unittest
from six import text_type, StringIO

from openmdao.core.problem import Problem, _get_implicit_connections
from openmdao.core.group import Group
from openmdao.core.problem import Relevance
from openmdao.components.paramcomp import ParamComp
from openmdao.components.execcomp import ExecComp
from openmdao.test.examplegroups import ExampleGroup, ExampleGroupWithPromotes

class TestGroup(unittest.TestCase):

    def test_add(self):

        group = Group()
        comp = ExecComp('y=x*2.0')
        group.add('mycomp', comp)

        subs = list(group.subsystems())
        self.assertEqual(len(subs), 1)
        self.assertEqual(subs[0], comp)
        self.assertEqual(subs[0].name, 'mycomp')

        comp2 = ExecComp('y=x*2.0')
        group.add("nextcomp", comp2)

        subs = list(group.subsystems())
        self.assertEqual(len(subs), 2)
        self.assertEqual(subs[0], comp)
        self.assertEqual(subs[1], comp2)

        with self.assertRaises(RuntimeError) as cm:
            group.add('mycomp', comp)

        expected_msg = "Group '' already contains a subsystem with name 'mycomp'."

        self.assertEqual(str(cm.exception), expected_msg)

    def test_variables(self):
        group = Group()
        group.add('C1', ExecComp('y=x*2.0'), promotes=['x'])
        group.add("C2", ExecComp('y=x*2.0'), promotes=['y'])

        # paths must be initialized prior to calling _setup_variables
        group._setup_paths('')
        params_dict, unknowns_dict = group._setup_variables()

        self.assertEqual(list(params_dict.keys()), ['C1.x', 'C2.x'])
        self.assertEqual(list(unknowns_dict.keys()), ['C1.y', 'C2.y'])

        self.assertEqual([m['promoted_name'] for n,m in params_dict.items()], ['x', 'C2.x'])
        self.assertEqual([m['promoted_name'] for n,m in unknowns_dict.items()], ['C1.y', 'y'])

    def test_multiple_connect(self):
        root = Group()
        C1 = root.add('C1', ExecComp('y=x*2.0'))
        C2 = root.add('C2', ExecComp('y=x*2.0'))
        C3 = root.add('C3', ExecComp('y=x*2.0'))

        root.connect('C1.y',['C2.x', 'C3.x'])

        root._setup_paths('')
        params_dict, unknowns_dict = root._setup_variables()

        # verify we get correct connection information
        connections = root._get_explicit_connections()
        expected_connections = {
            'C2.x': ['C1.y'],
            'C3.x': ['C1.y']
        }
        self.assertEqual(connections, expected_connections)

    def test_connect(self):
        root = ExampleGroup()
        prob = Problem(root=root)

        prob.setup(check=False)

        #root._setup_paths('')

        self.assertEqual(root.pathname, '')
        self.assertEqual(root.G3.pathname, 'G3')
        self.assertEqual(root.G2.pathname, 'G2')
        self.assertEqual(root.G1.pathname, 'G2.G1')

        # verify variables are set up correctly
        #root._setup_variables()

        # TODO: check for expected results from _setup_variables
        self.assertEqual(list(root.G1._params_dict.items()),
                         [('G2.G1.C2.x', {'shape': 1, 'pathname': 'G2.G1.C2.x', 'val': 3.0,
                                          'promoted_name': 'C2.x',
                                          'top_promoted_name': 'G2.G1.C2.x', 'size': 1})])
        self.assertEqual(list(root.G1._unknowns_dict.items()),
                         [('G2.G1.C2.y', {'shape': 1, 'pathname': 'G2.G1.C2.y', 'val': 5.5,
                                          'promoted_name': 'C2.y', 'top_promoted_name': 'G2.G1.C2.y',
                                          'size': 1})])

        self.assertEqual(list(root.G2._params_dict.items()),
                         [('G2.G1.C2.x', {'shape': 1, 'pathname': 'G2.G1.C2.x', 'val': 3.0,
                                          'promoted_name': 'G1.C2.x', 'top_promoted_name': 'G2.G1.C2.x',
                                          'size': 1})])
        self.assertEqual(list(root.G2._unknowns_dict.items()),
                         [('G2.C1.x', {'shape': 1, 'pathname': 'G2.C1.x', 'val': 5.0,
                                       'promoted_name': 'C1.x', 'top_promoted_name': 'G2.C1.x', 'size': 1}),
                          ('G2.G1.C2.y', {'shape': 1, 'pathname': 'G2.G1.C2.y', 'val': 5.5,
                                          'promoted_name': 'G1.C2.y', 'top_promoted_name': 'G2.G1.C2.y',
                                          'size': 1})])

        self.assertEqual(list(root.G3._params_dict.items()),
                         [('G3.C3.x', {'shape': 1, 'pathname': 'G3.C3.x', 'val': 3.0,
                                       'promoted_name': 'C3.x', 'top_promoted_name': 'G3.C3.x', 'size': 1}),
                          ('G3.C4.x', {'shape': 1, 'pathname': 'G3.C4.x', 'val': 3.0,
                                       'promoted_name': 'C4.x', 'top_promoted_name': 'G3.C4.x', 'size': 1})])
        self.assertEqual(list(root.G3._unknowns_dict.items()),
                         [('G3.C3.y', {'shape': 1, 'pathname': 'G3.C3.y', 'val': 5.5,
                                       'promoted_name': 'C3.y', 'top_promoted_name': 'G3.C3.y', 'size': 1}),
                          ('G3.C4.y', {'shape': 1, 'pathname': 'G3.C4.y', 'val': 5.5,
                                       'promoted_name': 'C4.y', 'top_promoted_name': 'G3.C4.y', 'size': 1})])

        self.assertEqual(list(root._params_dict.items()),
                         [('G2.G1.C2.x', {'shape': 1, 'pathname': 'G2.G1.C2.x', 'val': 3.0,
                                          'promoted_name': 'G2.G1.C2.x',
                                          'top_promoted_name': 'G2.G1.C2.x', 'size': 1}),
                          ('G3.C3.x', {'shape': 1, 'pathname': 'G3.C3.x', 'val': 3.0,
                                       'promoted_name': 'G3.C3.x', 'top_promoted_name': 'G3.C3.x', 'size': 1}),
                          ('G3.C4.x', {'shape': 1, 'pathname': 'G3.C4.x', 'val': 3.0,
                                       'promoted_name': 'G3.C4.x', 'top_promoted_name': 'G3.C4.x', 'size': 1})])
        self.assertEqual(list(root._unknowns_dict.items()),
                         [('G2.C1.x', {'shape': 1, 'pathname': 'G2.C1.x', 'val': 5.0,
                                       'promoted_name': 'G2.C1.x', 'top_promoted_name': 'G2.C1.x', 'size': 1}),
                          ('G2.G1.C2.y', {'shape': 1, 'pathname': 'G2.G1.C2.y', 'val': 5.5,
                                          'promoted_name': 'G2.G1.C2.y', 'top_promoted_name': 'G2.G1.C2.y',
                                          'size': 1}),
                          ('G3.C3.y', {'shape': 1, 'pathname': 'G3.C3.y', 'val': 5.5,
                                       'promoted_name': 'G3.C3.y', 'top_promoted_name': 'G3.C3.y', 'size': 1}),
                          ('G3.C4.y', {'shape': 1, 'pathname': 'G3.C4.y', 'val': 5.5,
                                       'promoted_name': 'G3.C4.y', 'top_promoted_name': 'G3.C4.y', 'size': 1})])

        # verify we get correct connection information
        #connections = root._get_explicit_connections()
        expected_connections = {
            'G2.G1.C2.x': 'G2.C1.x',
            'G3.C3.x':    'G2.G1.C2.y',
            'G3.C4.x':    'G3.C3.y'
        }
        self.assertEqual(root.connections, expected_connections)

        expected_root_params   = ['G3.C3.x']
        expected_root_unknowns = ['G2.C1.x', 'G2.G1.C2.y', 'G3.C3.y', 'G3.C4.y']

        expected_G3_params   = ['C4.x', 'C3.x']
        expected_G3_unknowns = ['C3.y', 'C4.y']

        expected_G2_params   = ['G1.C2.x']
        expected_G2_unknowns = ['C1.x', 'G1.C2.y']

        expected_G1_params   = ['C2.x']
        expected_G1_unknowns = ['C2.y']

        voi = None

        self.assertEqual(list(root.params.keys()),    expected_root_params)
        self.assertEqual(list(root.dpmat[voi].keys()),   expected_root_params)
        self.assertEqual(list(root.unknowns.keys()),  expected_root_unknowns)
        self.assertEqual(list(root.dumat[voi].keys()), expected_root_unknowns)
        self.assertEqual(list(root.resids.keys()),    expected_root_unknowns)
        self.assertEqual(list(root.drmat[voi].keys()),   expected_root_unknowns)

        self.assertEqual(list(root.G3.params.keys()),    expected_G3_params)
        self.assertEqual(list(root.G3.dpmat[voi].keys()),   expected_G3_params)
        self.assertEqual(list(root.G3.unknowns.keys()),  expected_G3_unknowns)
        self.assertEqual(list(root.G3.dumat[voi].keys()), expected_G3_unknowns)
        self.assertEqual(list(root.G3.resids.keys()),    expected_G3_unknowns)
        self.assertEqual(list(root.G3.drmat[voi].keys()),   expected_G3_unknowns)

        self.assertEqual(list(root.G2.params.keys()),    expected_G2_params)
        self.assertEqual(list(root.G2.dpmat[voi].keys()),   expected_G2_params)
        self.assertEqual(list(root.G2.unknowns.keys()),  expected_G2_unknowns)
        self.assertEqual(list(root.G2.dumat[voi].keys()), expected_G2_unknowns)
        self.assertEqual(list(root.G2.resids.keys()),    expected_G2_unknowns)
        self.assertEqual(list(root.G2.drmat[voi].keys()),   expected_G2_unknowns)

        self.assertEqual(list(root.G1.params.keys()),    expected_G1_params)
        self.assertEqual(list(root.G1.dpmat[voi].keys()),   expected_G1_params)
        self.assertEqual(list(root.G1.unknowns.keys()),  expected_G1_unknowns)
        self.assertEqual(list(root.G1.dumat[voi].keys()), expected_G1_unknowns)
        self.assertEqual(list(root.G1.resids.keys()),    expected_G1_unknowns)
        self.assertEqual(list(root.G1.drmat[voi].keys()),   expected_G1_unknowns)

        # verify subsystem is using shared view of parent unknowns vector
        root.unknowns['G2.C1.x'] = 99.
        self.assertEqual(root.G2.unknowns['C1.x'], 99.)

        # verify subsystem is getting correct metadata from parent unknowns vector
        self.assertEqual(root.unknowns.metadata('G2.C1.x'),
                         root.G2.unknowns.metadata('C1.x'))

    def test_promotes(self):
        root = ExampleGroupWithPromotes()
        prob = Problem(root=root)

        prob.setup(check=False)

        self.assertEqual(root.pathname, '')
        self.assertEqual(root.G3.pathname, 'G3')
        self.assertEqual(root.G2.pathname, 'G2')
        self.assertEqual(root.G1.pathname, 'G2.G1')

        # TODO: check for expected results from _setup_variables
        self.assertEqual(list(root.G1._params_dict.items()),
                         [('G2.G1.C2.x', {'shape': 1, 'pathname': 'G2.G1.C2.x', 'val': 3.0,
                                          'promoted_name': 'x', 'top_promoted_name': 'G2.x', 'size': 1})])
        self.assertEqual(list(root.G1._unknowns_dict.items()),
                         [('G2.G1.C2.y', {'shape': 1, 'pathname': 'G2.G1.C2.y', 'val': 5.5,
                                          'promoted_name': 'C2.y', 'top_promoted_name': 'G2.G1.C2.y', 'size': 1})])

        self.assertEqual(list(root.G2._params_dict.items()),
                         [('G2.G1.C2.x', {'shape': 1, 'pathname': 'G2.G1.C2.x', 'val': 3.0,
                                          'promoted_name': 'x', 'top_promoted_name': 'G2.x', 'size': 1})])
        self.assertEqual(list(root.G2._unknowns_dict.items()),
                         [('G2.C1.x', {'shape': 1, 'pathname': 'G2.C1.x', 'val': 5.0,
                                       'promoted_name': 'x', 'top_promoted_name': 'G2.x', 'size': 1}),
                          ('G2.G1.C2.y', {'shape': 1, 'pathname': 'G2.G1.C2.y', 'val': 5.5,
                                          'promoted_name': 'G1.C2.y', 'top_promoted_name': 'G2.G1.C2.y', 'size': 1})])

        self.assertEqual(list(root.G3._params_dict.items()),
                         [('G3.C3.x', {'shape': 1, 'pathname': 'G3.C3.x', 'val': 3.0,
                                       'promoted_name': 'C3.x', 'top_promoted_name': 'G3.C3.x', 'size': 1}),
                          ('G3.C4.x', {'shape': 1, 'pathname': 'G3.C4.x', 'val': 3.0,
                                       'promoted_name': 'x', 'top_promoted_name': 'x', 'size': 1})])

        self.assertEqual(list(root.G3._unknowns_dict.items()),
                         [('G3.C3.y', {'shape': 1, 'pathname': 'G3.C3.y', 'val': 5.5,
                                       'promoted_name': 'C3.y', 'top_promoted_name': 'G3.C3.y', 'size': 1}),
                          ('G3.C4.y', {'shape': 1, 'pathname': 'G3.C4.y', 'val': 5.5,
                                       'promoted_name': 'C4.y', 'top_promoted_name': 'G3.C4.y', 'size': 1})])

        self.assertEqual(list(root._params_dict.items()),
                         [('G2.G1.C2.x', {'shape': 1, 'pathname': 'G2.G1.C2.x', 'val': 3.0,
                                          'promoted_name': 'G2.x', 'top_promoted_name': 'G2.x', 'size': 1}),
                          ('G3.C3.x', {'shape': 1, 'pathname': 'G3.C3.x', 'val': 3.0,
                                       'promoted_name': 'G3.C3.x', 'top_promoted_name': 'G3.C3.x', 'size': 1}),
                          ('G3.C4.x', {'shape': 1, 'pathname': 'G3.C4.x', 'val': 3.0,
                                       'promoted_name': 'x', 'top_promoted_name': 'x', 'size': 1})])

        self.assertEqual(list(root._unknowns_dict.items()),
                         [('G2.C1.x', {'shape': 1, 'pathname': 'G2.C1.x', 'val': 5.0,
                                       'promoted_name': 'G2.x', 'top_promoted_name': 'G2.x', 'size': 1}),
                          ('G2.G1.C2.y', {'shape': 1, 'pathname': 'G2.G1.C2.y', 'val': 5.5,
                                          'promoted_name': 'G2.G1.C2.y', 'top_promoted_name': 'G2.G1.C2.y',
                                          'size': 1}),
                          ('G3.C3.y', {'shape': 1, 'pathname': 'G3.C3.y', 'val': 5.5,
                                       'promoted_name': 'G3.C3.y', 'top_promoted_name': 'G3.C3.y', 'size': 1}),
                          ('G3.C4.y', {'shape': 1, 'pathname': 'G3.C4.y', 'val': 5.5,
                                       'promoted_name': 'G3.C4.y', 'top_promoted_name': 'G3.C4.y', 'size': 1})])

        expected_root_params   = ['G3.C3.x']
        expected_root_unknowns = ['G2.x', 'G2.G1.C2.y', 'G3.C3.y', 'G3.C4.y']

        expected_G3_params   = ['C4.x', 'C3.x']
        expected_G3_unknowns = ['C3.y', 'C4.y']

        expected_G2_params   = ['G1.C2.x']
        expected_G2_unknowns = ['x', 'G1.C2.y']

        expected_G1_params   = ['C2.x']
        expected_G1_unknowns = ['C2.y']

        voi = None

        self.assertEqual(list(root.params.keys()),    expected_root_params)
        self.assertEqual(list(root.dpmat[voi].keys()),   expected_root_params)
        self.assertEqual(list(root.unknowns.keys()),  expected_root_unknowns)
        self.assertEqual(list(root.dumat[voi].keys()), expected_root_unknowns)
        self.assertEqual(list(root.resids.keys()),    expected_root_unknowns)
        self.assertEqual(list(root.drmat[voi].keys()),   expected_root_unknowns)

        self.assertEqual(list(root.G3.params.keys()),    expected_G3_params)
        self.assertEqual(list(root.G3.dpmat[voi].keys()),   expected_G3_params)
        self.assertEqual(list(root.G3.unknowns.keys()),  expected_G3_unknowns)
        self.assertEqual(list(root.G3.dumat[voi].keys()), expected_G3_unknowns)
        self.assertEqual(list(root.G3.resids.keys()),    expected_G3_unknowns)
        self.assertEqual(list(root.G3.drmat[voi].keys()),   expected_G3_unknowns)

        self.assertEqual(list(root.G2.params.keys()),    expected_G2_params)
        self.assertEqual(list(root.G2.dpmat[voi].keys()),   expected_G2_params)
        self.assertEqual(list(root.G2.unknowns.keys()),  expected_G2_unknowns)
        self.assertEqual(list(root.G2.dumat[voi].keys()), expected_G2_unknowns)
        self.assertEqual(list(root.G2.resids.keys()),    expected_G2_unknowns)
        self.assertEqual(list(root.G2.drmat[voi].keys()),   expected_G2_unknowns)

        self.assertEqual(list(root.G1.params.keys()),    expected_G1_params)
        self.assertEqual(list(root.G1.dpmat[voi].keys()),   expected_G1_params)
        self.assertEqual(list(root.G1.unknowns.keys()),  expected_G1_unknowns)
        self.assertEqual(list(root.G1.dumat[voi].keys()), expected_G1_unknowns)
        self.assertEqual(list(root.G1.resids.keys()),    expected_G1_unknowns)
        self.assertEqual(list(root.G1.drmat[voi].keys()),   expected_G1_unknowns)

        # verify subsystem is using shared view of parent unknowns vector
        root.unknowns['G2.x'] = 99.
        self.assertEqual(root.G2.unknowns['x'], 99.)

        # verify subsystem is getting correct metadata from parent unknowns vector
        self.assertEqual(root.unknowns.metadata('G2.x'),
                         root.G2.unknowns.metadata('x'))

    def test_variable_access(self):
        prob = Problem(root=ExampleGroup())

        # try accessing variable value before setup()
        try:
            prob['G2.C1.x']
        except Exception as err:
            msg = "'unknowns' has not been initialized, setup() must be called before 'G2.C1.x' can be accessed"
            self.assertEqual(text_type(err), msg)
        else:
            self.fail('Exception expected')

        prob.setup(check=False)

        # check that we can access values from unknowns (default) and params
        self.assertEqual(prob['G2.C1.x'], 5.)             # default output from ParamComp
        self.assertEqual(prob['G2.G1.C2.y'], 5.5)         # output from ExecComp
        self.assertEqual(prob.root.G3.C3.params['x'], 0.)      # initial value for a parameter
        self.assertEqual(prob.root.G2.G1.C2.params['x'], 0.)   # initial value for a parameter

        # now try same thing in a Group with promotes
        prob = Problem(root=ExampleGroupWithPromotes())
        prob.setup(check=False)

        prob.root.G2.unknowns['x'] = 99.

        self.assertEqual(prob['G2.x'],   99.)
        self.assertEqual(prob.root.G2.G1.C2.params['x'], 0.)   # initial value for a parameter

        # and make sure we get the correct value after a transfer
        prob.root.G2._transfer_data('G1')
        self.assertEqual(prob.root.G2.G1.C2.params['x'], 99.)  # transferred value of parameter

    def test_subsystem_access(self):
        prob = Problem(root=ExampleGroup())
        root = prob.root

        self.assertEqual(root.G2, prob.root.G2)
        self.assertEqual(root.G2.C1, prob.root.C1)
        self.assertEqual(root.G2.G1, prob.root.G1)
        self.assertEqual(root.G2.G1.C2, prob.root.C2)

        self.assertEqual(root.G3, prob.root.G3)
        self.assertEqual(root.G3.C3, prob.root.C3)
        self.assertEqual(root.G3.C4, prob.root.C4)

        prob = Problem(root=ExampleGroupWithPromotes())
        root = prob.root

        self.assertEqual(root.G2, prob.root.G2)
        self.assertEqual(root.G2.C1, prob.root.C1)
        self.assertEqual(root.G2.G1, prob.root.G1)
        self.assertEqual(root.G2.G1.C2, prob.root.C2)

        self.assertEqual(root.G3, prob.root.G3)
        self.assertEqual(root.G3.C3, prob.root.C3)
        self.assertEqual(root.G3.C4, prob.root.C4)

    def test_nested_conn(self):
        # tests a self contained connection under a Group nested at least 3 levels
        # down from the Problem
        prob = Problem(root=Group())
        root = prob.root
        G1 = root.add('G1', Group())
        G2 = G1.add('G2', Group())
        C1 = G2.add('C1', ParamComp('x', 5.))
        C2 = G2.add('C2', ExecComp('y=x*2.0'))
        G2.connect('C1.x', 'C2.x')
        prob.setup(check=False)

    def test_fd_params(self):
        # tests retrieval of a list of any internal params whose source is either
        # a ParamComp or is outside of the Group
        prob = Problem(root=ExampleGroup())
        prob.setup(check=False)
        root = prob.root

        self.assertEqual(root._get_fd_params(), ['G2.G1.C2.x'])
        self.assertEqual(root.G2._get_fd_params(), ['G1.C2.x'])
        self.assertEqual(root.G2.G1._get_fd_params(), ['C2.x'])
        self.assertEqual(root.G3._get_fd_params(), ['C3.x'])

        self.assertEqual(root.G3.C3._get_fd_params(), ['x'])
        self.assertEqual(root.G2.G1.C2._get_fd_params(), ['x'])

    def test_fd_unknowns(self):
        # tests retrieval of a list of any internal unknowns with ParamComp
        # variables filtered out.
        prob = Problem(root=ExampleGroup())
        prob.setup(check=False)
        root = prob.root

        self.assertEqual(root._get_fd_unknowns(), ['G2.G1.C2.y', 'G3.C3.y', 'G3.C4.y'])
        self.assertEqual(root.G2._get_fd_unknowns(), ['G1.C2.y'])
        self.assertEqual(root.G2.G1._get_fd_unknowns(), ['C2.y'])
        self.assertEqual(root.G3._get_fd_unknowns(), ['C3.y', 'C4.y'])

        self.assertEqual(root.G3.C3._get_fd_unknowns(), ['y'])
        self.assertEqual(root.G2.G1.C2._get_fd_unknowns(), ['y'])

    def test_dump(self):
        prob = Problem(root=ExampleGroup())
        prob.setup(check=False)
        save = StringIO()
        prob.root.dump(out_stream=save)

        # don't want to write a test that does a string compare of a dump, so
        # for now, just verify that calling dump doesn't raise an exception.

    def test_data_xfer(self):
        prob = Problem(root=ExampleGroupWithPromotes())
        prob.setup(check=False)

        prob.root.unknowns['G2.G1.C2.y'] = 99.
        self.assertEqual(prob['G2.G1.C2.y'], 99.)

        prob.root._transfer_data('G3')
        self.assertEqual(prob.root.params['G3.C3.x'], 99.)

        self.assertEqual(prob['G3.C3.x'], 99.)

    def test_list_and_set_order(self):

        prob = Problem(root=ExampleGroupWithPromotes())

        order1 = prob.root.list_order()
        self.assertEqual(order1, ['G2', 'G3'])

        # Big boy rules
        order2 = ['G3', 'G2']

        prob.root.set_order(order2)

        order1 = prob.root.list_order()
        self.assertEqual(order1, ['G3', 'G2'])

        # Extra
        order2 = ['G3', 'G2', 'junk']
        with self.assertRaises(ValueError) as cm:
            prob.root.set_order(order2)

        msg = "Unexpected new order. "
        msg += "The following are extra: ['junk']. "
        self.assertEqual(str(cm.exception), msg)

        # Missing
        order2 = ['G3']
        with self.assertRaises(ValueError) as cm:
            prob.root.set_order(order2)

        msg = "Unexpected new order. "
        msg += "The following are missing: ['G2']. "
        self.assertEqual(str(cm.exception), msg)

        # Extra and Missing
        order2 = ['G3', 'junk']
        with self.assertRaises(ValueError) as cm:
            prob.root.set_order(order2)

        msg = "Unexpected new order. "
        msg += "The following are missing: ['G2']. "
        msg += "The following are extra: ['junk']. "
        self.assertEqual(str(cm.exception), msg)

        # Dupes
        order2 = ['G3', 'G2', 'G3']
        with self.assertRaises(ValueError) as cm:
            prob.root.set_order(order2)

        msg = "Duplicate name found in order list: ['G3']"
        self.assertEqual(str(cm.exception), msg)

        # Don't let user call add.
        with self.assertRaises(RuntimeError) as cm:
            prob.root.add('C5', Group())

        msg = 'You cannot call add after specifying an order.'
        self.assertEqual(str(cm.exception), msg)

    def test_auto_order(self):
        # this tests the auto ordering when we have a cycle that is smaller
        # than the full graph.
        p = Problem(root=Group())
        root = p.root
        C5 = root.add("C5", ExecComp('y=x*2.0'))
        C6 = root.add("C6", ExecComp('y=x*2.0'))
        C1 = root.add("C1", ExecComp('y=x*2.0'))
        C2 = root.add("C2", ExecComp('y=x*2.0'))
        C3 = root.add("C3", ExecComp(['y=x*2.0','y2=x2+1.0']))
        C4 = root.add("C4", ExecComp(['y=x*2.0','y2=x2+1.0']))
        P1 = root.add("P1", ParamComp('x', 1.0))

        root.connect('P1.x', 'C1.x')
        root.connect('C1.y', 'C2.x')
        root.connect('C2.y', 'C4.x')
        root.connect('C4.y', 'C5.x')
        root.connect('C5.y', 'C6.x')
        root.connect('C5.y', 'C3.x2')
        root.connect('C6.y', 'C3.x')
        root.connect('C3.y', 'C4.x2')

        p.setup(check=False)

        self.assertEqual(p.root.list_auto_order(), ['P1','C1','C2','C4','C5','C6','C3'])

    def test_auto_order2(self):
        # this tests the auto ordering when we have a cycle that is the full graph.
        p = Problem(root=Group())
        root = p.root
        C1 = root.add("C1", ExecComp('y=x*2.0'))
        C2 = root.add("C2", ExecComp('y=x*2.0'))
        C3 = root.add("C3", ExecComp('y=x*2.0'))

        root.connect('C1.y', 'C3.x')
        root.connect('C3.y', 'C2.x')
        root.connect('C2.y', 'C1.x')

        p.setup(check=False)

        self.assertEqual(p.root.list_auto_order(), ['C1', 'C3', 'C2'])


if __name__ == "__main__":
    unittest.main()
