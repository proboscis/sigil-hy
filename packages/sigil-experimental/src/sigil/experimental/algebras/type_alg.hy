;;; algebras/type_alg.hy — TypeAlgebra: type inference + lift_n checking.
;;;
;;; Stateless: per-leaf type comes from meta["type"] (baked in by defprim /
;;; defask at declaration site). lift_n_ checks function annotations and
;;; raises on mismatch when strict=True.

(import inspect)
(import typing)


(defn _origin [t]
  (or (typing.get_origin t) t))

(defn _is-compat [actual expected]
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
  "Type inference + lift_n checking. No global state — per-leaf type lives
   in each Embed node's meta dict."

  (defn __init__ [self [strict True]]
    (setv self.strict strict))

  (defn pure_ [self value]
    (type value))

  (defn lift_n_ [self f arg-types]
    (setv sig (_signature f))
    (when (is sig None)
      (return object))
    (setv params (list (.values sig.parameters)))
    (when self.strict
      (when (> (len arg-types) (len params))
        (raise (TypeError
                f"lift-n: {f} takes {(len params)} args, got {(len arg-types)}")))
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

  (defn embed_ [self effect meta]
    (.get meta "type" object))

  (defn bind_ [self inner-type cont]
    object))
