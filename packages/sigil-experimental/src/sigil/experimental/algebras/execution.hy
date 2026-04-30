;;; algebras/execution.hy — convert apm AST into a doeff Program for run.
;;;
;;; Stateless w.r.t. registry. PrimEff impls come from the AST node's
;;; meta['impl'] (set by defprim :impl fn at declaration site).

(import doeff [Ask Pure])
(import doeff [do :as _doeff-do])
(import sigil.experimental.effects [AskEff PrimEff DoeffEff])


(defclass ExecutionAlgebra []
  "Build a doeff Program from the AST. Monad impl for run-apm."

  (defn pure_ [self value]
    (Pure value))

  (defn lift_n_ [self f progs]
    (defn _gen []
      (setv values [])
      (for [p progs]
        (setv v (yield p))
        (.append values v))
      (return (f #* values)))
    ((_doeff-do _gen)))

  (defn embed_ [self effect meta]
    (cond
      (isinstance effect AskEff)
      (Ask effect.key)

      (isinstance effect PrimEff)
      (do
        (when (not (in "impl" meta))
          (raise (ValueError
                  f"ExecutionAlgebra: no :impl in meta for '{effect.name}'. Use (defprim {effect.name} :impl fn).")))
        (Pure ((get meta "impl") #* effect.args)))

      (isinstance effect DoeffEff)
      effect.effect

      True
      (raise (TypeError f"ExecutionAlgebra: unknown effect {(type effect)}"))))

  (defn bind_ [self inner-prog cont]
    (import sigil.interp [interp])
    (defn _gen []
      (setv v (yield inner-prog))
      (setv next-prog (interp self (cont v)))
      (setv result (yield next-prog))
      (return result))
    ((_doeff-do _gen))))
