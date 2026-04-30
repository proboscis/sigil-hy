"""sigil-stdlib — Standard library for sigil-hy.

Bundled leaf types + algebras + runtime + variants. Built on top of the
``sigil`` core package. The doeff bridge (ExecutionAlgebra / run-apm /
DoeffEff use) is only available when ``sigil-stdlib-hy[doeff]`` is
installed; otherwise those names resolve to None.

Users may bypass this package entirely and build their own leaf types and
algebras directly on the ``sigil`` core.
"""
import hy.importer  # noqa: F401 — activates .hy import machinery

# Always available (no doeff dependency)
from sigil.stdlib.effects import (
    Effect, AskEff, PrimEff, DoeffEff,
    ask, prim, doeff,
)
from sigil.stdlib.algebras.deps     import DepsAlgebra
from sigil.stdlib.algebras.identity import IdentityAlgebra
from sigil.stdlib.algebras.cost     import CostAlgebra
from sigil.stdlib.algebras.type_alg import TypeAlgebra
from sigil.stdlib.control import when_of, if_of, while_of, times_of

# doeff-bridge (optional — None if doeff is not installed)
try:
    from sigil.stdlib.algebras.execution import ExecutionAlgebra
    from sigil.stdlib.run import run_apm, default_exec_algebra
except ImportError:
    ExecutionAlgebra = None
    run_apm = None
    default_exec_algebra = None


# ── Convenience shortcuts (built on stdlib algebras) ──────────────

from sigil import interp as _interp


def deps(ast):
    """Convenience: interp(DepsAlgebra(), ast)."""
    return _interp(DepsAlgebra(), ast)


def identity_eval(ast, env=None):
    """Convenience: interp(IdentityAlgebra(env=env), ast)."""
    return _interp(IdentityAlgebra(env=env), ast)


def to_program(ast):
    """Convenience: interp(ExecutionAlgebra(), ast). Requires the doeff extra."""
    if ExecutionAlgebra is None:
        raise ImportError(
            "to_program requires the doeff bridge: install with "
            "`pip install sigil-stdlib-hy[doeff]`"
        )
    return _interp(ExecutionAlgebra(), ast)
