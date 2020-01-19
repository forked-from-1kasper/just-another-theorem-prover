from functools import partial
from sys import argv

import sexpdata
from sexpdata import Symbol, Bracket

from prover.datatypes import Tree, Binding, State
from prover.prelude import *
from prover.errors import *
from prover.checker import check
from prover.parser import symbol, term

def axiom(curr, expr):
    name, *hypotheses, thesis = expr
    curr.context[symbol(name)] = Binding(maplist(partial(term, curr), hypotheses),
                                         term(curr, thesis))

def keyvalue(curr, pair):
    ident, τ = pair
    return (symbol(ident), term(curr, τ))

def genenv(curr, lst):
    return map(partial(keyvalue, curr),
               evensplit(lst))

def tree(curr, expr):
    ident, *rest, ptable = expr
    return Tree(symbol(ident),
                maplist(partial(tree, curr), rest),
                dict(genenv(curr, ptable)))

def theorem(curr, expr):
    ident, *xs, x, body = expr
    name = symbol(ident)
    hypotheses = maplist(second, genenv(curr, xs))
    thesis = term(curr, x)
    proof = tree(curr, body)

    τctx = curr.context.copy()
    for idx, value in genenv(curr, xs):
        τctx[idx] = Binding([], value)

    try:
        check(τctx, thesis, proof)
        print("“%s” checked" % name)
        curr.context[name] = Binding(hypotheses, thesis)
    except VerificationError as ex:
        print("“%s” has not been checked" % name)
        print("Error: %s" % ex.message)

def infix(curr, expr):
    name, prec = expr
    assert isinstance(prec, int), "precedence must be an integer"
    curr.infix[symbol(name)] = prec

def variables(curr, expr):
    curr.variables.extend(maplist(symbol, expr))

forms = {
    "axiom": axiom,
    "theorem": theorem,
    "lemma": theorem,
    "infix": infix,
    "variables": variables
}
def evaluate(curr, expr):
    head, *tail = expr
    form = symbol(head)

    assert form in forms, "unknown form “%s”" % form
    forms[form](curr, tail)

def doexprs(curr, string):
    curr.variables = []
    for expr in sexpdata.parse(string):
        evaluate(curr, expr)

appname, *filenames = argv
curr = State([], {}, {})
for filename in filenames:
    print("Checking %s" % filename)
    with open(filename, 'r', encoding='utf-8') as fin:
        doexprs(curr, fin.read())