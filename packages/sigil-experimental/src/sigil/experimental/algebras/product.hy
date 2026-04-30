;;; algebras/product.hy — ProductAlgebra: run N algebras in one AST walk.
;;;
;;; Each method delegates to all child algebras and returns a dict keyed by
;;; the algebra's name. lift_n_ transposes per-arg records into per-algebra
;;; arg tuples before delegating.

(defclass ProductAlgebra []
  "Compose multiple algebras; returns dict {name: F a} per node."

  (defn __init__ [self #** algebras]
    "ProductAlgebra :deps (DepsAlgebra) :cost (CostAlgebra)"
    (setv self.algebras algebras))

  (defn pure_ [self value]
    (dfor [n a] (.items self.algebras) n (.pure_ a value)))

  (defn lift_n_ [self f arg-records]
    (dfor [n a] (.items self.algebras)
          n (.lift_n_ a f (tuple (gfor rec arg-records (get rec n))))))

  (defn embed_ [self effect meta]
    (dfor [n a] (.items self.algebras) n (.embed_ a effect meta)))

  (defn bind_ [self inner-data cont]
    (dfor [n a] (.items self.algebras)
          n (.bind_ a (get inner-data n) cont))))
