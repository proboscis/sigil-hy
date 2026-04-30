"""sigil — Free Applicative + Algebraic Effects DSL for Hy (CORE).

This is a regular package whose subpackages may be provided by sibling
distributions (e.g. ``sigil-experimental-hy`` ships ``sigil.experimental``). The
``extend_path`` call below makes Python search every entry in sys.path
for ``sigil.<subpackage>`` rather than only this package's directory.


This package contains only the leaf-agnostic core:

  AST nodes:    Pure | Lift | Bind | Embed
  Constructors: pure / lift-n / bind / embed
                + list-of / dict-of / tuple-of / set-of (Lift sugar)
  Macros:       defapm / defapmk + walk-body / extract-clauses
  Interp:       generic (interp alg ast)
  Algebra:      base class (the protocol; no concrete algebras in core)
  Registry:     register-algebra + defprim / defask (kwargs forward)

The exploratory bundled extensions (AskEff/PrimEff/DoeffEff leaf types,
their algebras, run-apm, control combinators, defapmk variants) live in
the separate ``sigil-experimental-hy`` package as ``sigil.experimental``.
Those conventions are tentative — sigil and doeff have not agreed on a
canonical integration yet.

Originally:
``sigil-experimental-hy`` package.
"""
import hy.importer  # noqa: F401 — activates .hy import machinery

# Extend __path__ so sibling distributions (sigil-experimental-hy, ...) can ship
# subpackages of `sigil` from their own paths.
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

from sigil.ast import Pure, Lift, Bind, Embed, is_node
from sigil.constructors import (
    pure, lift_n, bind, embed,
    list_of, dict_of, tuple_of, set_of,
)
from sigil.interp import interp
from sigil.algebra import Algebra
