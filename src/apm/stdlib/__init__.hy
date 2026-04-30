;;; stdlib/__init__.hy — STANDARD LIBRARY for the apm DSL.
;;;
;;; NOT part of core. Bundles a default set of leaf types (AskEff / PrimEff),
;;; their constructors (apm-ask / apm-prim), and the algebras that interpret
;;; them (Deps / Cost / Type / Identity / Execution). Plus higher-level
;;; conveniences: run-apm, defapmk-typed, defapmk-checked.
;;;
;;; Users may bypass stdlib entirely and build their own leaf types +
;;; algebras on top of core. stdlib is one example domain.

(import apm.stdlib.effects             [Effect AskEff PrimEff
                                                          DoeffEff
                                                          apm-ask apm-prim
                                                          apm-doeff])
(import apm.stdlib.algebras.deps       [DepsAlgebra])
(import apm.stdlib.algebras.identity   [IdentityAlgebra])
(import apm.stdlib.algebras.execution  [ExecutionAlgebra])
(import apm.stdlib.algebras.cost       [CostAlgebra])
(import apm.stdlib.algebras.type_alg   [TypeAlgebra])
(import apm.stdlib.run                 [run-apm
                                                          default-exec-algebra])
(import apm.stdlib.control             [apm-when apm-if
                                                          apm-while apm-times])
