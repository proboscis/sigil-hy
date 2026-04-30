;;; stdlib/__init__.hy — STANDARD LIBRARY for the apm DSL.
;;;
;;; NOT part of core. Bundles a default set of leaf types and the algebras
;;; that interpret them. The doeff bridge (ExecutionAlgebra / run-apm) is
;;; only available when the `doeff` extra is installed (`pip install
;;; prism-hy[doeff]`); otherwise those names are left undefined.

;; ── Always available (no doeff dependency) ───────────────────────
(import prism.stdlib.effects           [Effect AskEff PrimEff DoeffEff
                                       apm-ask apm-prim apm-doeff])
(import prism.stdlib.algebras.deps     [DepsAlgebra])
(import prism.stdlib.algebras.identity [IdentityAlgebra])
(import prism.stdlib.algebras.cost     [CostAlgebra])
(import prism.stdlib.algebras.type_alg [TypeAlgebra])
(import prism.stdlib.control           [apm-when apm-if apm-while apm-times])

;; ── doeff-dependent (optional) ───────────────────────────────────
(try
  (do
    (import prism.stdlib.algebras.execution [ExecutionAlgebra])
    (import prism.stdlib.run                [run-apm default-exec-algebra]))
  (except [ImportError]
    (setv ExecutionAlgebra      None)
    (setv run-apm               None)
    (setv default-exec-algebra  None)))
