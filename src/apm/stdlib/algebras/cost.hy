;;; algebras/cost.hy — CostAlgebra: sum cost contributions.
;;;
;;; State: prim-costs / ask-costs tables populated via (defprim ... :cost X)
;;; and (defask ... :cost X). Bind returns inf — opaque continuation past
;;; the bind cannot be cost-bounded.

(import apm.stdlib.effects [AskEff PrimEff DoeffEff])


(defclass CostAlgebra []
  "Numeric cost upper bound, accumulated additively over Lift."

  (defn __init__ [self [prim-costs None] [ask-costs None] [default-prim 1.0] [default-ask 0.0]]
    (setv self.prim-costs (dict (or prim-costs {})))
    (setv self.ask-costs  (dict (or ask-costs  {})))
    (setv self.default-prim default-prim)
    (setv self.default-ask  default-ask))

  (defn pure_ [self value]
    0.0)

  (defn lift_n_ [self f args]
    (sum args))

  (defn eff_ [self effect]
    (cond
      (isinstance effect AskEff)
      (.get self.ask-costs effect.key self.default-ask)

      (isinstance effect PrimEff)
      (.get self.prim-costs effect.name self.default-prim)

      (isinstance effect DoeffEff)
      ;; Generic doeff effects: no static cost data — use default-prim.
      self.default-prim

      True
      (raise (TypeError f"CostAlgebra: unknown effect {(type effect)}"))))

  (defn bind_ [self inner-data cont]
    (float "inf"))

  (defn register-prim [self name #** kwargs]
    "Pick up :cost from defprim declarations."
    (when (in "cost" kwargs)
      (setv (get self.prim-costs name) (get kwargs "cost"))))

  (defn register-ask [self key #** kwargs]
    "Pick up :cost from defask declarations."
    (when (in "cost" kwargs)
      (setv (get self.ask-costs key) (get kwargs "cost")))))
