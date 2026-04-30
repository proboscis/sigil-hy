;;; algebras/execution.hy — convert apm AST into a doeff Program for run.
;;;
;;; PrimEff resolution: each ExecutionAlgebra carries an `impls` dict keyed
;;; by primitive name. (defprim name :impl fn) populates this via the
;;; register-prim hook. At run time, eff_ for a PrimEff calls the registered
;;; impl with the literal args (which were captured at AST construction).

(import doeff [Ask Pure])
(import doeff [do :as _doeff-do])
(import sigil.stdlib.effects [AskEff PrimEff DoeffEff])


(defclass ExecutionAlgebra []
  "Build a doeff Program from the AST. Monad impl for run-sigil.

   Pass `impls` at construction OR (more commonly) register the algebra and
   use defprim :impl fn to populate it incrementally."

  (defn __init__ [self [impls None]]
    (setv self.impls (dict (or impls {}))))

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

  (defn eff_ [self effect]
    (cond
      (isinstance effect AskEff)
      (Ask effect.key)

      (isinstance effect PrimEff)
      (do
        (when (not (in effect.name self.impls))
          (raise (ValueError
                  f"ExecutionAlgebra: no impl for primitive '{effect.name}'. Register via (defprim {effect.name} :impl fn).")))
        (Pure ((get self.impls effect.name) #* effect.args)))

      (isinstance effect DoeffEff)
      ;; Forward verbatim — caller must install the appropriate doeff handler.
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
    ((_doeff-do _gen)))

  (defn register-prim [self name #** kwargs]
    "Pick up :impl from defprim declarations."
    (when (in "impl" kwargs)
      (setv (get self.impls name) (get kwargs "impl"))))

  (defn register-ask [self key #** kwargs] None))
