;;; algebras/product.hy — ProductAlgebra: run N algebras in one AST walk.
;;;
;;; Each method delegates to all child algebras and returns a dict keyed by
;;; the algebra's registered name. lift_n_ transposes the per-arg dicts into
;;; per-algebra arg lists before delegating.

(defclass ProductAlgebra []
  "Compose multiple algebras; returns dict {name: F a} per node."

  (defn __init__ [self #** algebras]
    "ProductAlgebra :deps (DepsAlgebra) :cost (CostAlgebra)"
    (setv self.algebras algebras))

  (defn pure_ [self value]
    (dfor [n a] (.items self.algebras) n (.pure_ a value)))

  (defn lift_n_ [self f arg-records]
    ;; arg-records: tuple of dicts (one per Lift arg). Transpose per algebra.
    (dfor [n a] (.items self.algebras)
          n (.lift_n_ a f (tuple (gfor rec arg-records (get rec n))))))

  (defn embed_ [self effect]
    (dfor [n a] (.items self.algebras) n (.embed_ a effect)))

  (defn bind_ [self inner-data cont]
    (dfor [n a] (.items self.algebras)
          n (.bind_ a (get inner-data n) cont)))

  (defn register-prim [self name #** kwargs]
    (for [a (.values self.algebras)]
      (.register-prim a name #** kwargs)))

  (defn register-ask [self key #** kwargs]
    (for [a (.values self.algebras)]
      (.register-ask a key #** kwargs))))
