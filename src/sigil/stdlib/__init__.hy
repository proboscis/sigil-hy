;;; stdlib/__init__.hy — STANDARD LIBRARY for the apm DSL.
;;;
;;; NOT part of core. Bundles a default set of leaf types and the algebras
;;; that interpret them. The doeff bridge (ExecutionAlgebra / run-apm) is
;;; only available when the `doeff` extra is installed (`pip install
;;; sigil-hy[doeff]`); otherwise those names are left undefined.

;; ── Always available (no doeff dependency) ───────────────────────
(import sigil.stdlib.effects           [Effect AskEff PrimEff DoeffEff
                                       apm-ask apm-prim apm-doeff])
(import sigil.stdlib.algebras.deps     [DepsAlgebra])
(import sigil.stdlib.algebras.identity [IdentityAlgebra])
(import sigil.stdlib.algebras.cost     [CostAlgebra])
(import sigil.stdlib.algebras.type_alg [TypeAlgebra])
(import sigil.stdlib.control           [apm-when apm-if apm-while apm-times])

;; ── doeff-dependent (optional) ───────────────────────────────────
(try
  (do
    (import sigil.stdlib.algebras.execution [ExecutionAlgebra])
    (import sigil.stdlib.run                [run-apm default-exec-algebra]))
  (except [ImportError]
    (setv ExecutionAlgebra      None)
    (setv run-apm               None)
    (setv default-exec-algebra  None)))
