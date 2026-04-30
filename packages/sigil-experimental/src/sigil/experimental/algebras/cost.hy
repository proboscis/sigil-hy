;;; algebras/cost.hy — CostAlgebra: sum cost contributions read from meta.
;;;
;;; Stateless: each Embed node carries its own :cost in meta (set by defprim
;;; / defask at declaration site). Bind returns inf — opaque continuation
;;; past the bind cannot be cost-bounded.

(import sigil.experimental.effects [AskEff PrimEff DoeffEff])


(defclass CostAlgebra []
  "Numeric cost upper bound, accumulated additively over Lift."

  (defn __init__ [self [default 1.0]]
    (setv self.default default))

  (defn pure_ [self value]
    0.0)

  (defn lift_n_ [self f args]
    (sum args))

  (defn embed_ [self effect meta]
    (.get meta "cost" self.default))

  (defn bind_ [self inner-data cont]
    (float "inf")))
