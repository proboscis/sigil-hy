;;; algebras/identity.hy — IdentityAlgebra: eager pure eval (debug / testing).
;;;
;;; Stateless w.r.t. registry. AskEff keys resolve from the user-supplied
;;; env dict; PrimEff impls come from the AST node's meta["impl"] (set by
;;; defprim :impl fn at declaration site).

(import sigil.experimental.effects [AskEff PrimEff])


(defclass IdentityAlgebra []
  "No-effect eager evaluator. Asks resolve from `env`; Prims resolve from
   meta['impl'] on the Embed node."

  (defn __init__ [self [env None]]
    (setv self.env (dict (or env {}))))

  (defn pure_ [self value]
    value)

  (defn lift_n_ [self f args]
    (f #* args))

  (defn embed_ [self effect meta]
    (cond
      (isinstance effect AskEff)
      (do
        (when (not (in effect.key self.env))
          (raise (KeyError f"IdentityAlgebra: missing env key '{effect.key}'")))
        (get self.env effect.key))

      (isinstance effect PrimEff)
      (do
        (when (not (in "impl" meta))
          (raise (ValueError
                  f"IdentityAlgebra: no :impl in meta for '{effect.name}'")))
        ((get meta "impl") #* effect.args))

      True
      (raise (TypeError f"IdentityAlgebra: unknown effect {(type effect)}"))))

  (defn bind_ [self inner-data cont]
    (import sigil.interp [interp])
    (interp self (cont inner-data))))
