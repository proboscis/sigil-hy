;;; run.hy — execute an apm AST via DepsAlgebra (strict check) +
;;; ExecutionAlgebra (doeff Program).
;;;
;;; A module-level default ExecutionAlgebra is auto-registered, so any
;;; (defprim name :impl fn) declaration populates it without extra wiring.

(import doeff [WithHandler run])
(import doeff-core-effects.handlers [lazy-ask])
(import doeff-core-effects.scheduler [scheduled])

(import prism.interp              [interp])
(import prism.stdlib.algebras.deps       [DepsAlgebra])
(import prism.stdlib.algebras.execution  [ExecutionAlgebra])
(import prism.registry            [register-algebra])

;; Default ExecutionAlgebra used by run-prism. Auto-registered so defprim
;; :impl declarations populate it through the standard registry hook.
(setv default-exec-algebra (ExecutionAlgebra))
(register-algebra default-exec-algebra)


(defn run-apm [ast [env None] [strict True] [exec-alg None] [handlers None]]
  "Execute an apm AST. env supplies Ask resolutions for declared deps.

   strict=True:  raise ValueError if env is missing any DepsAlgebra-declared
                 key. Note: deps below a Bind are invisible (Algebra cap).
   strict=False: outer handlers may resolve missing keys.
   exec-alg:     override the default ExecutionAlgebra (e.g. for tests with
                 stub primitive impls).
   handlers:     list of doeff handlers to install in addition to lazy-ask.
                 Innermost-to-outermost. Use this when the AST contains
                 DoeffEff leaves whose effects need handlers (state, slog,
                 tell, time, ...). Each entry is a Program -> Program
                 callable or a raw @do-dispatcher."
  (setv env (dict (or env {})))
  (setv exec-alg (or exec-alg default-exec-algebra))
  (setv handlers (list (or handlers [])))
  (when strict
    (setv missing (- (interp (DepsAlgebra) ast) (set (.keys env))))
    (when missing
      (raise (ValueError f"apm requires deps not in env: {(sorted missing)}"))))
  (setv prog (interp exec-alg ast))
  ;; Install user-supplied handlers (innermost first), then lazy-ask outer.
  (setv composed prog)
  (for [h handlers]
    (setv composed (WithHandler h composed)))
  (setv composed (WithHandler (lazy-ask :env env) composed))
  (run (scheduled composed)))
