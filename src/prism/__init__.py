"""prism — Free Applicative + Algebraic Effects DSL for Hy.

Layering:
  CORE   — leaf-agnostic applicative+monad/effect AST + Algebra protocol
  STDLIB — example leaf types (AskEff/PrimEff/DoeffEff) + their algebras
           (Deps/Cost/Type/Identity) + control combinators

The doeff bridge (ExecutionAlgebra / run-apm) is only available when
``prism-hy[doeff]`` is installed; otherwise those names resolve to None.

Users may bypass STDLIB and define their own leaf types + algebras on top
of CORE. STDLIB is one example domain; CORE is the abstraction.
"""
import hy.importer  # noqa: F401 — activates .hy import machinery

# ── core ──────────────────────────────────────────────────────────
from prism.ast import Pure, Lift, Bind, Eff, is_node
from prism.constructors import (
    pure, lift_n, bind, eff,
    apm_list, apm_dict, apm_tuple, apm_set,
)
from prism.interp import interp
from prism.algebras import Algebra, ProductAlgebra
from prism.registry import (
    register_algebra, unregister_algebra,
    clear_registry, get_active_algebras,
)

# ── stdlib (default leaf types + algebras) ───────────────────────
from prism.stdlib import (
    Effect, AskEff, PrimEff, DoeffEff,
    apm_ask, apm_prim, apm_doeff,
    DepsAlgebra, IdentityAlgebra,
    CostAlgebra, TypeAlgebra,
    apm_when, apm_if, apm_while, apm_times,
)

# ── doeff bridge (optional — None if `prism-hy[doeff]` is not installed) ─
from prism.stdlib import (
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
    """Convenience: interp(ExecutionAlgebra(), ast). Requires prism-hy[doeff]."""
    if ExecutionAlgebra is None:
        raise ImportError(
            "to_program requires the doeff bridge: install with "
            "`pip install prism-hy[doeff]`"
        )
    return interp(ExecutionAlgebra(), ast)
