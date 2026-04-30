"""apm — Free Applicative + Algebraic Effects DSL for Hy.

Layering:
  CORE   — leaf-agnostic applicative+monad/effect AST + Algebra protocol
  STDLIB — example leaf types (AskEff/PrimEff/DoeffEff) + their algebras
           (Deps/Cost/Type/Identity/Execution) + run-apm + variants/control

Users may bypass STDLIB and define their own leaf types + algebras on top
of CORE. STDLIB is one example domain; CORE is the abstraction.
"""
import hy.importer  # noqa: F401 — activates .hy import machinery

# ── core ──────────────────────────────────────────────────────────
from apm.ast import Pure, Lift, Bind, Eff, is_node
from apm.constructors import (
    pure, lift_n, bind, eff,
    apm_list, apm_dict, apm_tuple, apm_set,
)
from apm.interp import interp
from apm.algebras import Algebra, ProductAlgebra
from apm.registry import (
    register_algebra, unregister_algebra,
    clear_registry, get_active_algebras,
)

# ── stdlib (default leaf types + algebras) ───────────────────────
from apm.stdlib import (
    Effect, AskEff, PrimEff, DoeffEff,
    apm_ask, apm_prim, apm_doeff,
    DepsAlgebra, IdentityAlgebra, ExecutionAlgebra,
    CostAlgebra, TypeAlgebra,
    run_apm, default_exec_algebra,
    apm_when, apm_if, apm_while, apm_times,
)


def deps(ast):
    """Convenience: interp(DepsAlgebra(), ast)."""
    return interp(DepsAlgebra(), ast)


def identity_eval(ast, env=None):
    """Convenience: interp(IdentityAlgebra(env=env), ast)."""
    return interp(IdentityAlgebra(env=env), ast)


def to_program(ast):
    """Convenience: interp(ExecutionAlgebra(), ast)."""
    return interp(ExecutionAlgebra(), ast)
