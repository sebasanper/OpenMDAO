
from openmdao.components.execcomp import ExecComp


class ConstraintComp(ExecComp):
    """
    A Component that represents an equality or inequality constraint.

    Args
    ----
    expr : str
        Constraint expression containing an operator that is
        one of ['<', '>', '<=', '>=', '='].

    outname : str, optional
        Name of the output variable containing the result of the
        constraint equation.  Default is 'out'.

    """

    def __init__(self, expr, out='out'):
        newexpr = _combined_expr(expr)
        super(ConstraintComp, self).__init__("%s = %s" % (out, newexpr))


def _combined_expr(expr):
    """Given a constraint object, take the lhs, operator, and
    rhs and combine them into a single expression by moving rhs
    terms over to the lhs.  For example,
    for the constraint 'C1.x < C2.y + 7', return the expression
    'C1.x - C2.y - 7'.  Depending on the direction of the operator,
    the sign of the expression may be flipped.  The final form of
    the constraint, when evaluated, will be considered to be satisfied
    if it evaluates to a value <= 0.
    """
    lhs, op, rhs = _parse_constraint(expr)

    first, second = (rhs, lhs) if op.startswith('>') else (lhs, rhs)

    try:
        if float(first) == 0:
            return "-(%s)" % second
    except Exception:
        pass

    try:
        if float(second) == 0.:
            return first
    except Exception:
        pass

    return '%s-(%s)' % (first, second)


def _parse_constraint(expr_string):
    """ Parses the constraint expression string and returns the lhs string,
    the rhs string, and comparator
    """
    for comparator in ['==', '>=', '<=', '>', '<', '=']:
        parts = expr_string.split(comparator)
        if len(parts) == 2:
            # check for == because otherwise they get a cryptic error msg
            if comparator == '==':
                break
            return (parts[0].strip(), comparator, parts[1].strip())
        # elif len(parts) == 3:
        #     return (parts[1].strip(), comparator,
        #             (parts[0].strip(), parts[2].strip()))

    msg = "Constraints require an explicit comparator (=, <, >, <=, or >=)"
    raise ValueError(msg)
