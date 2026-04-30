;;; algebra.hy — CORE Algebra protocol (base class only).
;;;
;;; Core ships only the abstract protocol. Concrete algebras live in
;;; extension packages such as sigil-experimental-hy. Core is purely the
;;; applicative+monad/effect SYNTAX abstraction; any actual computation
;;; (= an algebra implementation) is the user's choice and lives outside.
;;;
;;; No global state, no registry, no register hooks. AST nodes are
;;; self-describing — Embed carries a meta dict that algebras read for
;;; per-leaf annotations. There is no out-of-band channel.


(defclass Algebra []
  "Base class. Subclasses must implement the four fold methods.

   Required:
     pure_(self, value)            : a -> F a
     lift_n_(self, f, args)        : (b1->...->bn->a, [F b]) -> F a
     embed_(self, effect, meta)    : (leaf, dict) -> F a
                                     algebras dispatch on type(effect) and
                                     read per-leaf annotations from meta
     bind_(self, inner-data, cont) : (F a, a -> Apm b) -> F b"

  (defn _name [self]
    (. (type self) __name__))

  (defn pure_ [self value]
    (raise (NotImplementedError f"{(._name self)}.pure_ not implemented")))

  (defn lift_n_ [self f args]
    (raise (NotImplementedError f"{(._name self)}.lift_n_ not implemented")))

  (defn embed_ [self effect meta]
    (raise (NotImplementedError f"{(._name self)}.embed_ not implemented")))

  (defn bind_ [self inner-data cont]
    (raise (NotImplementedError f"{(._name self)}.bind_ not implemented"))))
