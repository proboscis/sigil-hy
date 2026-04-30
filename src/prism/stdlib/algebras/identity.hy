;;; algebras/identity.hy — IdentityAlgebra: eager pure eval (debug / testing).
;;;
;;; Looks up Ask keys in a plain dict env. PrimEff is resolved via `impls`
;;; (populated either at construction or by defprim :impl fn registration).

(import prism.stdlib.effects [AskEff PrimEff])


(defclass IdentityAlgebra []
  "No-effect eager evaluator. Asks resolve from `env`; Prims resolve from
   `impls` (or raise if unknown)."

  (defn __init__ [self [env None] [impls None]]
    (setv self.env   (dict (or env   {})))
    (setv self.impls (dict (or impls {}))))

  (defn pure_ [self value]
    value)

  (defn lift_n_ [self f args]
    (f #* args))

  (defn eff_ [self effect]
    (cond
      (isinstance effect AskEff)
      (do
        (when (not (in effect.key self.env))
          (raise (KeyError f"IdentityAlgebra: missing env key '{effect.key}'")))
        (get self.env effect.key))

      (isinstance effect PrimEff)
      (do
        (when (not (in effect.name self.impls))
          (raise (ValueError
                  f"IdentityAlgebra: no impl for primitive '{effect.name}'")))
        ((get self.impls effect.name) #* effect.args))

      True
      (raise (TypeError f"IdentityAlgebra: unknown effect {(type effect)}"))))

  (defn bind_ [self inner-data cont]
    (import prism.interp [interp])
    (interp self (cont inner-data)))

  (defn register-prim [self name #** kwargs]
    (when (in "impl" kwargs)
      (setv (get self.impls name) (get kwargs "impl"))))

  (defn register-ask [self key #** kwargs] None))
