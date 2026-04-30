;;; run.hy — execute a sigil AST via DepsAlgebra (strict check) +
;;; ExecutionAlgebra (doeff Program). No global state — each run-apm
;;; call constructs its own algebra instances.

(import doeff [WithHandler run])
(import doeff-core-effects.handlers [lazy-ask])
(import doeff-core-effects.scheduler [scheduled])

(import sigil.interp                          [interp])
(import sigil.experimental.algebras.deps      [DepsAlgebra])
(import sigil.experimental.algebras.execution [ExecutionAlgebra])


(defn run-apm [ast [env None] [strict True] [exec-alg None] [handlers None]]
  "Execute a sigil AST. env supplies Ask resolutions for declared deps.

   strict=True:  raise ValueError if env is missing any DepsAlgebra-declared
                 key. Note: deps below a Bind are invisible (Algebra cap).
   strict=False: outer handlers may resolve missing keys.
   exec-alg:     override the default ExecutionAlgebra (e.g. for tests).
   handlers:     list of doeff handlers to install in addition to lazy-ask.
                 Innermost-to-outermost. Use this when the AST contains
                 DoeffEff leaves whose effects need handlers (state, slog,
                 tell, time, ...). Each entry is a Program -> Program
                 callable or a raw @do-dispatcher."
  (setv env (dict (or env {})))
  (setv exec-alg (or exec-alg (ExecutionAlgebra)))
  (setv handlers (list (or handlers [])))
  (when strict
    (setv missing (- (interp (DepsAlgebra) ast) (set (.keys env))))
    (when missing
      (raise (ValueError f"apm requires deps not in env: {(sorted missing)}"))))
  (setv prog (interp exec-alg ast))
  (setv composed prog)
  (for [h handlers]
    (setv composed (WithHandler h composed)))
  (setv composed (WithHandler (lazy-ask :env env) composed))
  (run (scheduled composed)))
