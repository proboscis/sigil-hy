"""sigil — Free Applicative + Algebraic Effects DSL for Hy.

Layering:
  CORE   — leaf-agnostic applicative+monad/effect AST + Algebra protocol
  STDLIB — example leaf types (AskEff/PrimEff/DoeffEff) + their algebras
           (Deps/Cost/Type/Identity) + control combinators

The doeff bridge (ExecutionAlgebra / run-apm) is only available when
``sigil-hy[doeff]`` is installed; otherwise those names resolve to None.

Users may bypass STDLIB and define their own leaf types + algebras on top
of CORE. STDLIB is one example domain; CORE is the abstraction.
"""
import hy.importer  # noqa: F401 — activates .hy import machinery

# ── core ──────────────────────────────────────────────────────────
from sigil.ast import Pure, Lift, Bind, Eff, is_node
from sigil.constructors import (
    pure, lift_n, bind, eff,
    apm_list, apm_dict, apm_tuple, apm_set,
)
from sigil.interp import interp
from sigil.algebras import Algebra, ProductAlgebra
from sigil.registry import (
    register_algebra, unregister_algebra,
    clear_registry, get_active_algebras,
)

# ── stdlib (default leaf types + algebras) ───────────────────────
from sigil.stdlib import (
    Effect, AskEff, PrimEff, DoeffEff,
    apm_ask, apm_prim, apm_doeff,
    DepsAlgebra, IdentityAlgebra,
    CostAlgebra, TypeAlgebra,
    apm_when, apm_if, apm_while, apm_times,
)

# ── doeff bridge (optional — None if `sigil-hy[doeff]` is not installed) ─
from sigil.stdlib import (
    ExecutionAlgebra,
    run_apm,
    default_exec_algebra,
)


def deps(ast):
    """Convenience: interp(DepsAlgebra(), ast)."""
    return interp(DepsAlgebra(), ast)


def identity_eval(ast, env=None):
    """Convenience: interp(IdentityAlgebra(env=env), ast)."""
    return interp(IdentityAlgebra(env=env), ast)


def to_program(ast):
    """Convenience: interp(ExecutionAlgebra(), ast). Requires sigil-hy[doeff]."""
    if ExecutionAlgebra is None:
        raise ImportError(
            "to_program requires the doeff bridge: install with "
            "`pip install sigil-hy[doeff]`"
        )
    return interp(ExecutionAlgebra(), ast)
