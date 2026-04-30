"""Tests for sigil + sigil.stdlib — Free Applicative over Free Monad/Effect DSL.

defapm / defapmk emit AST nodes (Pure / Lift / Bind / Embed). Applicative /
monad/effect semantics live in Algebra implementations.
"""
import hy  # noqa: F401 — activates Hy import hook
import pytest

import sigil  # noqa: F401 — registers .hyk/.hyp loaders
import sigil.stdlib  # noqa: F401

# ── core ──────────────────────────────────────────────────────────
from sigil import (
    dict_of,
    list_of,
    set_of,
    tuple_of,
    is_node,
    lift_n,
    pure,
)

# ── stdlib ────────────────────────────────────────────────────────
from sigil.stdlib import (
    ask,
    deps,
    identity_eval,
    run_apm,
)


# ── AST construction + interpreters ────────────────────────────────


def test_pure_node_and_run():
    a = pure(42)
    assert is_node(a)
    assert deps(a) == frozenset()
    assert identity_eval(a) == 42
    assert run_apm(a) == 42


def test_ask_deps_and_run():
    a = ask("threshold")
    assert deps(a) == frozenset({"threshold"})
    assert run_apm(a, env={"threshold": 0.5}) == 0.5
    assert identity_eval(a, env={"threshold": 0.5}) == 0.5


def test_lift_n_deps_union():
    a = ask("x")
    b = ask("y")
    combined = lift_n(lambda x, y: x + y, a, b)
    assert deps(combined) == frozenset({"x", "y"})
    assert run_apm(combined, env={"x": 3, "y": 4}) == 7


def test_list_of_mixed():
    a = ask("a")
    result = list_of(a, pure(99), pure("lit"))
    assert deps(result) == frozenset({"a"})
    assert run_apm(result, env={"a": 1}) == [1, 99, "lit"]


def test_dict_of():
    a = ask("threshold")
    result = dict_of("thr", a, "max", pure(100))
    assert deps(result) == frozenset({"threshold"})
    assert run_apm(result, env={"threshold": 0.5}) == {"thr": 0.5, "max": 100}


def test_tuple_of():
    a = ask("p")
    b = ask("q")
    result = tuple_of(a, b)
    assert deps(result) == frozenset({"p", "q"})
    assert run_apm(result, env={"p": 1, "q": 2}) == (1, 2)


def test_set_of():
    a = ask("a")
    b = ask("b")
    result = set_of(a, b)
    assert deps(result) == frozenset({"a", "b"})
    assert run_apm(result, env={"a": "x", "b": "y"}) == frozenset({"x", "y"})


def test_run_strict_rejects_missing_dep():
    with pytest.raises(ValueError, match="deps not in env"):
        run_apm(ask("missing-key"))


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
(import sigil.stdlib [ask])
(defapm threshold (ask "threshold"))
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
(import sigil [list-of pure]) (import sigil.stdlib [ask])
(defapmk pair []
  [(ask "x") (ask "y")])
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
(import sigil [list-of pure]) (import sigil.stdlib [ask])
(defapmk mixed []
  [(ask "a") 99 "lit"])
"""
    )
    result = mod.mixed()
    assert deps(result) == frozenset({"a"})
    assert run_apm(result, env={"a": 1}) == [1, 99, "lit"]


def test_macro_defapmk_dict_literal():
    mod = _hy_eval(
        """
(require sigil.macros [defapmk])
(import sigil [dict-of pure]) (import sigil.stdlib [ask])
(defapmk config []
  {"thr"  (ask "threshold")
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
(import sigil [tuple-of pure]) (import sigil.stdlib [ask])
(defapmk pair-tuple []
  #((ask "p") (ask "q")))
"""
    )
    result = mod.pair_tuple()
    assert deps(result) == frozenset({"p", "q"})
    assert run_apm(result, env={"p": 1, "q": 2}) == (1, 2)


def test_macro_defapmk_set_literal():
    mod = _hy_eval(
        """
(require sigil.macros [defapmk])
(import sigil [set-of pure]) (import sigil.stdlib [ask])
(defapmk syms []
  #{(ask "a") (ask "b")})
"""
    )
    result = mod.syms()
    assert deps(result) == frozenset({"a", "b"})
    assert run_apm(result, env={"a": "x", "b": "y"}) == frozenset({"x", "y"})


def test_macro_defapmk_with_args():
    mod = _hy_eval(
        """
(require sigil.macros [defapm defapmk])
(import sigil [lift-n pure]) (import sigil.stdlib [ask])
(import operator)
(defapm thr (ask "thr"))
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
(import sigil [list-of dict-of pure]) (import sigil.stdlib [ask])
(defapmk nested []
  {"items" [(ask "a") (ask "b")]
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

    inner = ask("seed")
    # cont decides at runtime which apm to return — analysis can't see "fork"
    cont = lambda v: ask("fork") if v > 0 else pure(0)
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

    node = bind(ask("x"), lambda v: pure(v * 2))
    assert identity_eval(node, env={"x": 5}) == 10


# ── Algebra interpreter pattern + registry ─────────────────────────


def test_algebra_interp_basic():
    """interp(alg, ast) folds the AST through alg's four methods."""
    from sigil import (
        ProductAlgebra,
        interp,
    )
    from sigil.stdlib import (
        CostAlgebra,
        DepsAlgebra,
        ExecutionAlgebra,
        IdentityAlgebra,
    )
    from doeff import WithHandler, run as doeff_run
    from doeff_core_effects.handlers import lazy_ask
    from doeff_core_effects.scheduler import scheduled

    ast = lift_n(lambda x, y: x + y, ask("x"), ask("y"))

    assert interp(DepsAlgebra(), ast) == frozenset({"x", "y"})
    assert interp(IdentityAlgebra(env={"x": 3, "y": 4}), ast) == 7

    # ExecutionAlgebra produces a doeff Program; run it to get value
    prog = interp(ExecutionAlgebra(), ast)
    composed = WithHandler(lazy_ask(env={"x": 3, "y": 4}), prog)
    assert doeff_run(scheduled(composed)) == 7


def test_product_algebra_one_walk():
    """ProductAlgebra runs N algebras in one AST traversal."""
    from sigil import (
        ProductAlgebra,
        interp,
    )
    from sigil.stdlib import (
        CostAlgebra,
        DepsAlgebra,
    )

    cost = CostAlgebra(default_ask=2.0)
    prod = ProductAlgebra(deps=DepsAlgebra(), cost=cost)

    ast = lift_n(lambda x, y: x + y, ask("x"), ask("y"))
    result = interp(prod, ast)

    assert result == {"deps": frozenset({"x", "y"}), "cost": 4.0}


def test_defprim_defask_open_kwargs():
    """defprim and defask forward kwargs to every active algebra; each
    algebra picks up only the keys it cares about."""
    import hy  # noqa: F401
    from sigil import (
        ProductAlgebra,
        clear_registry,
        get_active_algebras,
        interp,
        register_algebra,
    )
    from sigil.stdlib import (
        CostAlgebra,
        DepsAlgebra,
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
    from sigil import interp
    from sigil.stdlib import TypeAlgebra

    def add(x: int, y: int) -> int:
        return x + y

    ast = lift_n(add, pure(3), pure(4))
    assert interp(TypeAlgebra(), ast) is int


def test_type_algebra_raises_on_mismatch():
    """lift_n raises TypeError when an arg type is incompatible with f's
    parameter annotation."""
    from sigil import interp
    from sigil.stdlib import TypeAlgebra

    def expect_str(s: str) -> int:
        return len(s)

    ast = lift_n(expect_str, pure(42))
    with pytest.raises(TypeError, match="not compatible with"):
        interp(TypeAlgebra(), ast)


def test_type_algebra_pulls_types_from_defprim_defask():
    """defprim :type and defask :type populate TypeAlgebra's tables."""
    import hy  # noqa: F401
    from sigil import (
        clear_registry,
        interp,
        register_algebra,
    )
    from sigil.stdlib import (
        TypeAlgebra,
        prim,
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
    assert interp(talg, ask("threshold")) is float
    assert interp(talg, prim("fetch-news", "BTC")) is list


def test_type_algebra_strict_off_only_infers():
    """strict=False means lift_n won't raise on mismatch — only infer."""
    from sigil import interp
    from sigil.stdlib import TypeAlgebra

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
(import  sigil [pure lift-n]) (import sigil.stdlib [DepsAlgebra TypeAlgebra])

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
        clear_registry,
        register_algebra,
    )
    from sigil.stdlib import (
        prim,
        default_exec_algebra,
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
    assert run_apm(prim("sym-len", "BTCUSDT")) == 7
    assert run_apm(prim("concat", "a", "b", "c")) == "abc"

    # Compose with lift_n: feed prim-result into another function
    ast = lift_n(lambda n: n * 2, prim("sym-len", "ETHUSDT"))
    assert run_apm(ast) == 14


def test_prim_eff_unknown_raises():
    """PrimEff without registered impl raises a clear error at execution."""
    from sigil import (
        clear_registry,
        register_algebra,
    )
    from sigil.stdlib import (
        prim,
        default_exec_algebra,
    )

    clear_registry()
    register_algebra(default_exec_algebra)
    default_exec_algebra.impls.clear()

    with pytest.raises(ValueError, match="no impl for primitive 'never-defined'"):
        run_apm(prim("never-defined"))


def test_prim_eff_isolated_exec_alg_for_test():
    """Pass a fresh ExecutionAlgebra to run-apm to stub primitives in tests."""
    from sigil import (
        clear_registry,
        register_algebra,
    )
    from sigil.stdlib import (
        ExecutionAlgebra,
        prim,
        default_exec_algebra,
    )

    clear_registry()
    register_algebra(default_exec_algebra)

    # Production exec-alg has no impls
    default_exec_algebra.impls.clear()

    # Test exec-alg with a stub
    test_exec = ExecutionAlgebra(impls={"fetch-news": lambda sym: f"stub-news-for-{sym}"})

    assert run_apm(prim("fetch-news", "BTC"), exec_alg=test_exec) == "stub-news-for-BTC"


def test_doeff_state_through_sigil():
    """doeff Get/Put state effects flow through apm via DoeffEff +
    a state handler passed to run-sigil. apm acts as the syntactic frontend
    while doeff drives execution."""
    from doeff_core_effects.effects import Get, Put
    from doeff_core_effects.handlers import state

    from sigil import bind, pure
    from sigil.stdlib import doeff

    # Read counter, write counter+1, return new value
    ast = bind(
        doeff(Get("counter")),
        lambda n: bind(
            doeff(Put("counter", n + 1)),
            lambda _: pure(n + 1),
        ),
    )
    result = run_apm(ast, env={}, handlers=[state(initial={"counter": 41})])
    assert result == 42


def test_doeff_eff_in_lift_n():
    """DoeffEff leaves compose with lift_n the same as any other apm value."""
    from doeff_core_effects.effects import Get
    from doeff_core_effects.handlers import state

    from sigil.stdlib import doeff

    ast = lift_n(
        lambda x, y: x + y,
        doeff(Get("a")),
        doeff(Get("b")),
    )
    result = run_apm(
        ast, env={}, handlers=[state(initial={"a": 10, "b": 32})]
    )
    assert result == 42


def test_while_of_with_doeff_state():
    """while-of + doeff state effect: runtime loop, lazy AST via Bind cont."""
    from doeff_core_effects.effects import Get, Put
    from doeff_core_effects.handlers import state

    from sigil import bind, pure
    from sigil.stdlib import doeff, while_of

    ast = while_of(
        bind(doeff(Get("n")), lambda n: pure(n > 0)),
        bind(doeff(Get("n")), lambda n: doeff(Put("n", n - 1))),
    )
    run_apm(ast, env={}, handlers=[state(initial={"n": 7})])
    # No way to query terminal state without an extra effect; observe via second AST
    final = run_apm(
        bind(
            while_of(
                bind(doeff(Get("k")), lambda k: pure(k > 0)),
                bind(doeff(Get("k")), lambda k: doeff(Put("k", k - 1))),
            ),
            lambda _: doeff(Get("k")),
        ),
        env={},
        handlers=[state(initial={"k": 7})],
    )
    assert final == 0


def test_while_of_long_loop_does_not_blow_stack():
    """5000 iterations finish — doeff VM trampolines Bind/cont steps."""
    import sys
    from doeff_core_effects.effects import Get, Put
    from doeff_core_effects.handlers import state

    from sigil import bind, pure
    from sigil.stdlib import doeff, while_of

    sys.setrecursionlimit(10000)
    ast = while_of(
        bind(doeff(Get("n")), lambda n: pure(n > 0)),
        bind(doeff(Get("n")), lambda n: doeff(Put("n", n - 1))),
    )
    run_apm(ast, env={}, handlers=[state(initial={"n": 5000})])  # no exception


def test_user_defined_leaf_via_generic_eff():
    """`embed` wraps arbitrary user-domain values; algebras dispatch on type.

    Demonstrates that AskEff/PrimEff are NOT core — the user can define their
    own leaf type and write an algebra that interprets it."""
    from dataclasses import dataclass

    from sigil import Algebra, Pure, Lift, Bind, Embed, embed
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

        def embed_(self, leaf):
            if isinstance(leaf, FetchPrice):
                return self.prices[leaf.symbol]
            if isinstance(leaf, CurrentTime):
                return self.now
            raise TypeError(f"unsupported leaf {type(leaf)}")

        def bind_(self, inner, cont):
            return interp(self, cont(inner))

    ast = lift_n(
        lambda p, t: f"{t}: {p}",
        embed(FetchPrice("BTC")),
        embed(CurrentTime()),
    )

    alg = MyDomainAlgebra(prices={"BTC": 65000.0}, now="2026-04-30T12:00")
    assert interp(alg, ast) == "2026-04-30T12:00: 65000.0"


def test_extensible_new_algebra_no_core_change():
    """Adding a brand-new analysis = subclass Algebra, register it. Core
    (AST / constructors / macros / defprim / interp) is untouched."""
    from sigil import (
        Algebra,
        clear_registry,
        interp,
        register_algebra,
    )
    from sigil.stdlib import (
        AskEff,
        PrimEff,
    )

    class ProvenanceAlgebra(Algebra):
        def __init__(self):
            self.prim_prov: dict[str, str] = {}

        def pure_(self, value):
            return frozenset()

        def lift_n_(self, f, args):
            return frozenset().union(*args)

        def embed_(self, effect):
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
    from sigil.stdlib import prim
    ast = lift_n(
        lambda a, b, c: (a, b, c),
        prim("fetch-news", "BTC"),
        prim("local-cache"),
        ask("user.session"),
    )
    assert interp(prov, ast) == frozenset(
        {"polygon-v2", "memory", "ask:user.session"}
    )
