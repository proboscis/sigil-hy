"""Tests for apm — Free Applicative over Free Monad DSL.

defapm / defapmk emit AST nodes (Pure / Lift / Bind / Eff). All applicative /
monad semantics live in interpreters under sigil.interp.
"""
import hy  # noqa: F401 — activates Hy import hook
import pytest

import sigil  # noqa: F401 — registers .hyk/.hyp loaders
from sigil import (
    apm_ask,
    apm_dict,
    apm_list,
    apm_set,
    apm_tuple,
    deps,
    identity_eval,
    is_node,
    lift_n,
    pure,
    run_apm,
)


# ── AST construction + interpreters ────────────────────────────────


def test_pure_node_and_run():
    a = pure(42)
    assert is_node(a)
    assert deps(a) == frozenset()
    assert identity_eval(a) == 42
    assert run_apm(a) == 42


def test_apm_ask_deps_and_run():
    a = apm_ask("threshold")
    assert deps(a) == frozenset({"threshold"})
    assert run_apm(a, env={"threshold": 0.5}) == 0.5
    assert identity_eval(a, env={"threshold": 0.5}) == 0.5


def test_lift_n_deps_union():
    a = apm_ask("x")
    b = apm_ask("y")
    combined = lift_n(lambda x, y: x + y, a, b)
    assert deps(combined) == frozenset({"x", "y"})
    assert run_apm(combined, env={"x": 3, "y": 4}) == 7


def test_apm_list_mixed():
    a = apm_ask("a")
    result = apm_list(a, pure(99), pure("lit"))
    assert deps(result) == frozenset({"a"})
    assert run_apm(result, env={"a": 1}) == [1, 99, "lit"]


def test_apm_dict():
    a = apm_ask("threshold")
    result = apm_dict("thr", a, "max", pure(100))
    assert deps(result) == frozenset({"threshold"})
    assert run_apm(result, env={"threshold": 0.5}) == {"thr": 0.5, "max": 100}


def test_apm_tuple():
    a = apm_ask("p")
    b = apm_ask("q")
    result = apm_tuple(a, b)
    assert deps(result) == frozenset({"p", "q"})
    assert run_apm(result, env={"p": 1, "q": 2}) == (1, 2)


def test_apm_set():
    a = apm_ask("a")
    b = apm_ask("b")
    result = apm_set(a, b)
    assert deps(result) == frozenset({"a", "b"})
    assert run_apm(result, env={"a": "x", "b": "y"}) == frozenset({"x", "y"})


def test_run_apm_strict_rejects_missing_dep():
    with pytest.raises(ValueError, match="deps not in env"):
        run_apm(apm_ask("missing-key"))


# ── Macros (compiled inline via hy.eval) ───────────────────────────


def _hy_eval(src: str):
    """Compile and evaluate Hy source in a fresh module-like namespace."""
    import types

    mod = types.ModuleType("__apm_test__")
    mod.__dict__["__builtins__"] = __builtins__
    code = hy.read_many(src)
    hy.eval(hy.models.Expression([hy.models.Symbol("do"), *code]), mod.__dict__)
    return mod


def test_macro_defapm_constant():
    mod = _hy_eval(
        """
(require sigil.macros [defapm])
(import sigil [apm-ask])
(defapm threshold (apm-ask "threshold"))
"""
    )
    assert is_node(mod.threshold)
    assert deps(mod.threshold) == frozenset({"threshold"})
    assert run_apm(mod.threshold, env={"threshold": 0.7}) == 0.7


def test_macro_defapmk_literal():
    mod = _hy_eval(
        """
(require sigil.macros [defapmk])
(import sigil [pure])
(defapmk const-42 [] 42)
"""
    )
    result = mod.const_42()
    assert is_node(result)
    assert deps(result) == frozenset()
    assert run_apm(result) == 42


def test_macro_defapmk_list_literal():
    mod = _hy_eval(
        """
(require sigil.macros [defapmk])
(import sigil [apm-ask apm-list pure])
(defapmk pair []
  [(apm-ask "x") (apm-ask "y")])
"""
    )
    result = mod.pair()
    assert is_node(result)
    assert deps(result) == frozenset({"x", "y"})
    assert run_apm(result, env={"x": 10, "y": 20}) == [10, 20]


def test_macro_defapmk_list_mixed():
    mod = _hy_eval(
        """
(require sigil.macros [defapmk])
(import sigil [apm-ask apm-list pure])
(defapmk mixed []
  [(apm-ask "a") 99 "lit"])
"""
    )
    result = mod.mixed()
    assert deps(result) == frozenset({"a"})
    assert run_apm(result, env={"a": 1}) == [1, 99, "lit"]


def test_macro_defapmk_dict_literal():
    mod = _hy_eval(
        """
(require sigil.macros [defapmk])
(import sigil [apm-ask apm-dict pure])
(defapmk config []
  {"thr"  (apm-ask "threshold")
   "max"  100
   "name" "strategy-a"})
"""
    )
    result = mod.config()
    assert deps(result) == frozenset({"threshold"})
    out = run_apm(result, env={"threshold": 0.5})
    assert out == {"thr": 0.5, "max": 100, "name": "strategy-a"}


def test_macro_defapmk_tuple_literal():
    mod = _hy_eval(
        """
(require sigil.macros [defapmk])
(import sigil [apm-ask apm-tuple pure])
(defapmk pair-tuple []
  #((apm-ask "p") (apm-ask "q")))
"""
    )
    result = mod.pair_tuple()
    assert deps(result) == frozenset({"p", "q"})
    assert run_apm(result, env={"p": 1, "q": 2}) == (1, 2)


def test_macro_defapmk_set_literal():
    mod = _hy_eval(
        """
(require sigil.macros [defapmk])
(import sigil [apm-ask apm-set pure])
(defapmk syms []
  #{(apm-ask "a") (apm-ask "b")})
"""
    )
    result = mod.syms()
    assert deps(result) == frozenset({"a", "b"})
    assert run_apm(result, env={"a": "x", "b": "y"}) == frozenset({"x", "y"})


def test_macro_defapmk_with_args():
    mod = _hy_eval(
        """
(require sigil.macros [defapm defapmk])
(import sigil [apm-ask lift-n pure])
(import operator)
(defapm thr (apm-ask "thr"))
(defapmk score [data]
  (lift-n operator.mul data thr))
"""
    )
    result = mod.score(pure(10))
    assert deps(result) == frozenset({"thr"})
    assert run_apm(result, env={"thr": 3}) == 30


def test_macro_defapmk_nested_structural():
    mod = _hy_eval(
        """
(require sigil.macros [defapmk])
(import sigil [apm-ask apm-list apm-dict pure])
(defapmk nested []
  {"items" [(apm-ask "a") (apm-ask "b")]
   "count" 2})
"""
    )
    result = mod.nested()
    assert deps(result) == frozenset({"a", "b"})
    out = run_apm(result, env={"a": 1, "b": 2})
    assert out == {"items": [1, 2], "count": 2}


# ── Bind — monadic escape ──────────────────────────────────────────


def test_bind_static_deps_capped_below_continuation():
    """Bind's continuation is opaque — deps undercounts post-bind keys."""
    from doeff import UnhandledEffect

    from sigil import bind

    inner = apm_ask("seed")
    # cont decides at runtime which apm to return — analysis can't see "fork"
    cont = lambda v: apm_ask("fork") if v > 0 else pure(0)
    node = bind(inner, cont)

    # static analysis only sees inner's deps; "fork" stays hidden
    assert deps(node) == frozenset({"seed"})

    # strict-mode dep check does NOT catch the missing "fork" because deps
    # cannot see it — execution is what fails when fork is absent
    with pytest.raises(UnhandledEffect):
        run_apm(node, env={"seed": 1})

    # supply the hidden dep too and execution completes
    assert run_apm(node, env={"seed": 1, "fork": 99}) == 99


def test_bind_via_identity_eval():
    """Bind threads value through cont in the identity interpreter too."""
    from sigil import bind

    node = bind(apm_ask("x"), lambda v: pure(v * 2))
    assert identity_eval(node, env={"x": 5}) == 10


# ── Algebra interpreter pattern + registry ─────────────────────────


def test_algebra_interp_basic():
    """interp(alg, ast) folds the AST through alg's four methods."""
    from sigil import (
        DepsAlgebra,
        CostAlgebra,
        IdentityAlgebra,
        ExecutionAlgebra,
        ProductAlgebra,
        interp,
    )
    from doeff import WithHandler, run as doeff_run
    from doeff_core_effects.handlers import lazy_ask
    from doeff_core_effects.scheduler import scheduled

    ast = lift_n(lambda x, y: x + y, apm_ask("x"), apm_ask("y"))

    assert interp(DepsAlgebra(), ast) == frozenset({"x", "y"})
    assert interp(IdentityAlgebra(env={"x": 3, "y": 4}), ast) == 7

    # ExecutionAlgebra produces a doeff Program; run it to get value
    prog = interp(ExecutionAlgebra(), ast)
    composed = WithHandler(lazy_ask(env={"x": 3, "y": 4}), prog)
    assert doeff_run(scheduled(composed)) == 7


def test_product_algebra_one_walk():
    """ProductAlgebra runs N algebras in one AST traversal."""
    from sigil import (
        DepsAlgebra,
        CostAlgebra,
        ProductAlgebra,
        interp,
    )

    cost = CostAlgebra(default_ask=2.0)
    prod = ProductAlgebra(deps=DepsAlgebra(), cost=cost)

    ast = lift_n(lambda x, y: x + y, apm_ask("x"), apm_ask("y"))
    result = interp(prod, ast)

    assert result == {"deps": frozenset({"x", "y"}), "cost": 4.0}


def test_defprim_defask_open_kwargs():
    """defprim and defask forward kwargs to every active algebra; each
    algebra picks up only the keys it cares about."""
    import hy  # noqa: F401
    from sigil import (
        CostAlgebra,
        DepsAlgebra,
        ProductAlgebra,
        clear_registry,
        get_active_algebras,
        interp,
        register_algebra,
    )

    clear_registry()
    deps_alg = DepsAlgebra()
    cost_alg = CostAlgebra()
    register_algebra(deps_alg)
    register_algebra(cost_alg)
    assert len(get_active_algebras()) == 2

    src = """
(require sigil.registry [defprim defask])

(defprim fetch-news :cost 100 :provenance "polygon-v2")
(defprim score-symbol :cost 5)
(defask threshold :cost 0.5)
"""
    hy.eval(hy.models.Expression([hy.models.Symbol("do"), *hy.read_many(src)]))

    # CostAlgebra picked up :cost on each declaration
    assert cost_alg.prim_costs == {"fetch-news": 100, "score-symbol": 5}
    assert cost_alg.ask_costs == {"threshold": 0.5}
    # :provenance was forwarded but no algebra in the registry cared


def test_type_algebra_infers_return_type():
    """TypeAlgebra reads f's return annotation as the lift_n result type."""
    from sigil import TypeAlgebra, interp

    def add(x: int, y: int) -> int:
        return x + y

    ast = lift_n(add, pure(3), pure(4))
    assert interp(TypeAlgebra(), ast) is int


def test_type_algebra_raises_on_mismatch():
    """lift_n raises TypeError when an arg type is incompatible with f's
    parameter annotation."""
    from sigil import TypeAlgebra, interp

    def expect_str(s: str) -> int:
        return len(s)

    ast = lift_n(expect_str, pure(42))
    with pytest.raises(TypeError, match="not compatible with"):
        interp(TypeAlgebra(), ast)


def test_type_algebra_pulls_types_from_defprim_defask():
    """defprim :type and defask :type populate TypeAlgebra's tables."""
    import hy  # noqa: F401
    from sigil import (
        TypeAlgebra,
        apm_prim,
        clear_registry,
        interp,
        register_algebra,
    )

    clear_registry()
    talg = TypeAlgebra()
    register_algebra(talg)

    src = """
(require sigil.registry [defprim defask])
(defprim fetch-news :type list)
(defask threshold :type float)
"""
    hy.eval(hy.models.Expression([hy.models.Symbol("do"), *hy.read_many(src)]))

    assert talg.prim_types == {"fetch-news": list}
    assert talg.ask_types == {"threshold": float}

    # Use them in an AST and verify the inferred result type
    assert interp(talg, apm_ask("threshold")) is float
    assert interp(talg, apm_prim("fetch-news", "BTC")) is list


def test_type_algebra_strict_off_only_infers():
    """strict=False means lift_n won't raise on mismatch — only infer."""
    from sigil import TypeAlgebra, interp

    def expect_str(s: str) -> int:
        return len(s)

    ast = lift_n(expect_str, pure(42))
    assert interp(TypeAlgebra(strict=False), ast) is int  # no raise


def test_defapmk_typed_variant_catches_type_mismatch():
    """defapmk-typed wraps defapmk with TypeAlgebra; mismatch raises at call."""
    import hy  # noqa: F401
    mod = _hy_eval(
        """
(require sigil.macros   [defapmk])
(require sigil.stdlib.variants [defapmk-typed])
(import  sigil [pure lift-n])

(defn add-ints [#^ int x #^ int y] (+ x y))

(defapmk-typed good-call [data]
  :returns int
  (lift-n add-ints data (pure 3)))

(defapmk-typed bad-call [data]
  :returns int
  (lift-n add-ints (pure "not an int") data))
"""
    )
    # good call returns a typed AST
    ast = mod.good_call(pure(5))
    assert run_apm(ast) == 8

    # bad call raises immediately on the call (TypeAlgebra catches mismatch)
    with pytest.raises(TypeError, match="not compatible with"):
        mod.bad_call(pure(5))


def test_defapmk_checked_variant_runs_arbitrary_algebras():
    """defapmk-checked accepts any Algebra list and runs all on each call."""
    import hy  # noqa: F401
    mod = _hy_eval(
        """
(require sigil.macros   [defapmk])
(require sigil.stdlib.variants [defapmk-checked])
(import  sigil [pure lift-n DepsAlgebra TypeAlgebra])

(defn mul-floats [#^ float x #^ float y] (* x y))

(defapmk-checked safe-mul [a b]
  :check [(DepsAlgebra) (TypeAlgebra)]
  (lift-n mul-floats a b))
"""
    )
    # both checks pass
    ast = mod.safe_mul(pure(2.0), pure(3.0))
    assert run_apm(ast) == 6.0

    # TypeAlgebra catches a string in float position
    with pytest.raises(TypeError, match="not compatible with"):
        mod.safe_mul(pure("oops"), pure(3.0))


def test_prim_eff_executes_via_registered_impl():
    """defprim :impl populates ExecutionAlgebra; AST with PrimEff runs."""
    import hy  # noqa: F401
    from sigil import (
        apm_prim,
        clear_registry,
        default_exec_algebra,
        register_algebra,
    )

    clear_registry()
    register_algebra(default_exec_algebra)
    default_exec_algebra.impls.clear()

    src = """
(require sigil.registry [defprim])
(defprim sym-len :impl len)
(defprim concat :impl (fn [#* xs] (.join "" xs)))
"""
    hy.eval(hy.models.Expression([hy.models.Symbol("do"), *hy.read_many(src)]))

    # PrimEff with literal args resolves through the registered impl
    assert run_apm(apm_prim("sym-len", "BTCUSDT")) == 7
    assert run_apm(apm_prim("concat", "a", "b", "c")) == "abc"

    # Compose with lift_n: feed prim-result into another function
    ast = lift_n(lambda n: n * 2, apm_prim("sym-len", "ETHUSDT"))
    assert run_apm(ast) == 14


def test_prim_eff_unknown_raises():
    """PrimEff without registered impl raises a clear error at execution."""
    from sigil import (
        apm_prim,
        clear_registry,
        default_exec_algebra,
        register_algebra,
    )

    clear_registry()
    register_algebra(default_exec_algebra)
    default_exec_algebra.impls.clear()

    with pytest.raises(ValueError, match="no impl for primitive 'never-defined'"):
        run_apm(apm_prim("never-defined"))


def test_prim_eff_isolated_exec_alg_for_test():
    """Pass a fresh ExecutionAlgebra to run-apm to stub primitives in tests."""
    from sigil import (
        ExecutionAlgebra,
        apm_prim,
        clear_registry,
        register_algebra,
        default_exec_algebra,
    )

    clear_registry()
    register_algebra(default_exec_algebra)

    # Production exec-alg has no impls
    default_exec_algebra.impls.clear()

    # Test exec-alg with a stub
    test_exec = ExecutionAlgebra(impls={"fetch-news": lambda sym: f"stub-news-for-{sym}"})

    assert run_apm(apm_prim("fetch-news", "BTC"), exec_alg=test_exec) == "stub-news-for-BTC"


def test_doeff_state_through_apm():
    """doeff Get/Put state effects flow through apm via DoeffEff +
    a state handler passed to run-sigil. apm acts as the syntactic frontend
    while doeff drives execution."""
    from doeff_core_effects.effects import Get, Put
    from doeff_core_effects.handlers import state

    from sigil import apm_doeff, bind, pure

    # Read counter, write counter+1, return new value
    ast = bind(
        apm_doeff(Get("counter")),
        lambda n: bind(
            apm_doeff(Put("counter", n + 1)),
            lambda _: pure(n + 1),
        ),
    )
    result = run_apm(ast, env={}, handlers=[state(initial={"counter": 41})])
    assert result == 42


def test_doeff_eff_in_lift_n():
    """DoeffEff leaves compose with lift_n the same as any other apm value."""
    from doeff_core_effects.effects import Get
    from doeff_core_effects.handlers import state

    from sigil import apm_doeff

    ast = lift_n(
        lambda x, y: x + y,
        apm_doeff(Get("a")),
        apm_doeff(Get("b")),
    )
    result = run_apm(
        ast, env={}, handlers=[state(initial={"a": 10, "b": 32})]
    )
    assert result == 42


def test_apm_while_with_doeff_state():
    """apm-while + doeff state effect: runtime loop, lazy AST via Bind cont."""
    from doeff_core_effects.effects import Get, Put
    from doeff_core_effects.handlers import state

    from sigil import apm_doeff, apm_while, bind, pure

    ast = apm_while(
        bind(apm_doeff(Get("n")), lambda n: pure(n > 0)),
        bind(apm_doeff(Get("n")), lambda n: apm_doeff(Put("n", n - 1))),
    )
    run_apm(ast, env={}, handlers=[state(initial={"n": 7})])
    # No way to query terminal state without an extra effect; observe via second AST
    final = run_apm(
        bind(
            apm_while(
                bind(apm_doeff(Get("k")), lambda k: pure(k > 0)),
                bind(apm_doeff(Get("k")), lambda k: apm_doeff(Put("k", k - 1))),
            ),
            lambda _: apm_doeff(Get("k")),
        ),
        env={},
        handlers=[state(initial={"k": 7})],
    )
    assert final == 0


def test_apm_while_long_loop_does_not_blow_stack():
    """5000 iterations finish — doeff VM trampolines Bind/cont steps."""
    import sys
    from doeff_core_effects.effects import Get, Put
    from doeff_core_effects.handlers import state

    from sigil import apm_doeff, apm_while, bind, pure

    sys.setrecursionlimit(10000)
    ast = apm_while(
        bind(apm_doeff(Get("n")), lambda n: pure(n > 0)),
        bind(apm_doeff(Get("n")), lambda n: apm_doeff(Put("n", n - 1))),
    )
    run_apm(ast, env={}, handlers=[state(initial={"n": 5000})])  # no exception


def test_user_defined_leaf_via_generic_eff():
    """`eff` wraps arbitrary user-domain values; algebras dispatch on type.

    Demonstrates that AskEff/PrimEff are NOT core — the user can define their
    own leaf type and write an algebra that interprets it."""
    from dataclasses import dataclass

    from sigil import Algebra, Pure, Lift, Bind, Eff, eff
    from sigil import interp, lift_n, pure as apm_pure

    @dataclass(frozen=True)
    class FetchPrice:
        symbol: str

    @dataclass(frozen=True)
    class CurrentTime:
        pass

    class MyDomainAlgebra(Algebra):
        """Eager evaluator that recognises FetchPrice and CurrentTime — and
        nothing else (not AskEff / PrimEff)."""

        def __init__(self, prices, now):
            self.prices = prices
            self.now = now

        def pure_(self, v):
            return v

        def lift_n_(self, f, args):
            return f(*args)

        def eff_(self, leaf):
            if isinstance(leaf, FetchPrice):
                return self.prices[leaf.symbol]
            if isinstance(leaf, CurrentTime):
                return self.now
            raise TypeError(f"unsupported leaf {type(leaf)}")

        def bind_(self, inner, cont):
            return interp(self, cont(inner))

    ast = lift_n(
        lambda p, t: f"{t}: {p}",
        eff(FetchPrice("BTC")),
        eff(CurrentTime()),
    )

    alg = MyDomainAlgebra(prices={"BTC": 65000.0}, now="2026-04-30T12:00")
    assert interp(alg, ast) == "2026-04-30T12:00: 65000.0"


def test_extensible_new_algebra_no_core_change():
    """Adding a brand-new analysis = subclass Algebra, register it. Core
    (AST / constructors / macros / defprim / interp) is untouched."""
    from sigil import (
        AskEff,
        Algebra,
        PrimEff,
        clear_registry,
        interp,
        register_algebra,
    )

    class ProvenanceAlgebra(Algebra):
        def __init__(self):
            self.prim_prov: dict[str, str] = {}

        def pure_(self, value):
            return frozenset()

        def lift_n_(self, f, args):
            return frozenset().union(*args)

        def eff_(self, effect):
            if isinstance(effect, AskEff):
                return frozenset({f"ask:{effect.key}"})
            if isinstance(effect, PrimEff):
                return frozenset({self.prim_prov.get(effect.name, "?")})
            raise TypeError(effect)

        def bind_(self, inner_data, cont):
            return inner_data

        def register_prim(self, name, **kwargs):
            if "provenance" in kwargs:
                self.prim_prov[name] = kwargs["provenance"]

        def register_ask(self, key, **kwargs):
            return None

    clear_registry()
    prov = ProvenanceAlgebra()
    register_algebra(prov)

    import hy  # noqa: F401
    src = """
(require sigil.registry [defprim])
(defprim fetch-news :cost 100 :provenance "polygon-v2")
(defprim local-cache :provenance "memory")
"""
    hy.eval(hy.models.Expression([hy.models.Symbol("do"), *hy.read_many(src)]))

    assert prov.prim_prov == {
        "fetch-news": "polygon-v2",
        "local-cache": "memory",
    }

    # Build an AST that uses the registered primitives
    from sigil import apm_prim
    ast = lift_n(
        lambda a, b, c: (a, b, c),
        apm_prim("fetch-news", "BTC"),
        apm_prim("local-cache"),
        apm_ask("user.session"),
    )
    assert interp(prov, ast) == frozenset(
        {"polygon-v2", "memory", "ask:user.session"}
    )
