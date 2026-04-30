;;; algebras/__init__.hy — CORE Algebra protocol + leaf-agnostic algebras.
;;;
;;; Core means: works for any leaf type the user defines. Specifically:
;;;   - Algebra: 4-method protocol base class
;;;   - ProductAlgebra: zip N algebras into one walk (works on any leaves)
;;;
;;; Leaf-aware bundled algebras (Deps, Cost, Type, Execution, Identity) live
;;; under sigil.stdlib.algebras — they assume AskEff/PrimEff.


(defclass Algebra []
  "Base class. Subclasses must implement pure_, lift_n_, eff_, bind_.

   Required:
     pure_(self, value)            : a -> F a
     lift_n_(self, f, args)        : (b1->...->bn->a, [F b]) -> F a
     eff_(self, leaf-value)        : leaf -> F a   (algebra dispatches on
                                                    type(leaf-value))
     bind_(self, inner-data, cont) : (F a, a -> Apm b) -> F b

   Optional hooks (default no-op):
     register-prim(self, name, **kwargs)  — invoked by (defprim name ...)
     register-ask (self, key,  **kwargs)  — invoked by (defask  key  ...)"

  (defn _name [self]
    (. (type self) __name__))

  (defn pure_ [self value]
    (raise (NotImplementedError f"{(._name self)}.pure_ not implemented")))

  (defn lift_n_ [self f args]
    (raise (NotImplementedError f"{(._name self)}.lift_n_ not implemented")))

  (defn eff_ [self effect]
    (raise (NotImplementedError f"{(._name self)}.eff_ not implemented")))

  (defn bind_ [self inner-data cont]
    (raise (NotImplementedError f"{(._name self)}.bind_ not implemented")))

  (defn register-prim [self name #** kwargs] None)
  (defn register-ask  [self key  #** kwargs] None))


(import sigil.algebras.product [ProductAlgebra])
