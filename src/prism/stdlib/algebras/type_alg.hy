;;; algebras/type_alg.hy — TypeAlgebra: type inference + lift_n checking.
;;;
;;; Walks the AST and returns the inferred type at each node. lift_n_ checks
;;; that arg types match the function's parameter annotations and raises
;;; TypeError on mismatch (when strict=True).
;;;
;;; Limitations (v0):
;;;   - object / typing.Any treated as wildcard top
;;;   - Generics (List[int], Dict[K,V]) compared by origin only — not deep
;;;   - No polymorphism / type variable unification
;;;   - Bind returns object (cont's return type unknown)

(import inspect)
(import typing)
(import prism.stdlib.effects [AskEff PrimEff DoeffEff])


(defn _origin [t]
  "Strip parametric generics: List[int] -> list, Dict[K,V] -> dict, else t."
  (or (typing.get_origin t) t))

(defn _is-compat [actual expected]
  "Check that actual <: expected. Conservative; treats Any/object as top."
  (cond
    (or (is expected object) (is expected typing.Any)) True
    (or (is actual   object) (is actual   typing.Any)) True
    (= actual expected) True
    True
    (try
      (issubclass (_origin actual) (_origin expected))
      (except [TypeError] False))))


(defn _signature [f]
  (try
    (inspect.signature f)
    (except [Exception] None)))


(defclass TypeAlgebra []
  "Type inference + lift_n checking.

   register-prim / register-ask consume :type kwargs from defprim / defask."

  (defn __init__ [self [strict True]]
    (setv self.strict strict)
    (setv self.prim-types {})
    (setv self.ask-types  {}))

  (defn pure_ [self value]
    (type value))

  (defn lift_n_ [self f arg-types]
    (setv sig (_signature f))
    (when (is sig None)
      (return object))
    (setv params (list (.values sig.parameters)))
    (when self.strict
      ;; arg count check (skip *args / **kwargs heuristic — keep simple)
      (when (> (len arg-types) (len params))
        (raise (TypeError
                f"lift-n: {f} takes {(len params)} args, got {(len arg-types)}")))
      ;; per-arg compatibility
      (for [#(i actual) (enumerate arg-types)]
        (setv param (get params i))
        (setv expected param.annotation)
        (when (is expected inspect.Parameter.empty)
          (continue))
        (when (not (_is-compat actual expected))
          (raise (TypeError
                  f"lift-n: arg {i} of {f}: type {actual} not compatible with {expected}")))))
    (setv ret sig.return_annotation)
    (if (is ret inspect.Signature.empty) object ret))

  (defn eff_ [self effect]
    (cond
      (isinstance effect AskEff)
      (.get self.ask-types effect.key object)

      (isinstance effect PrimEff)
      (.get self.prim-types effect.name object)

      (isinstance effect DoeffEff)
      ;; Generic doeff effects: no static type info — top.
      object

      True
      (raise (TypeError f"TypeAlgebra: unknown effect {(type effect)}"))))

  (defn bind_ [self inner-type cont]
    object)   ; cont's return type cannot be inferred without running it

  (defn register-prim [self name #** kwargs]
    (when (in "type" kwargs)
      (setv (get self.prim-types name) (get kwargs "type"))))

  (defn register-ask [self key #** kwargs]
    (when (in "type" kwargs)
      (setv (get self.ask-types key) (get kwargs "type")))))
