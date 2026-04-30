;;; algebras/deps.hy — DepsAlgebra: collect deps from each Embed's meta.
;;;
;;; No leaf-type dispatch. Each Embed node declares its own deps via
;;; meta["deps"] (a frozenset of keys). Bind caps analysis (cont opaque).

(defclass DepsAlgebra []
  "Union of meta['deps'] over reachable Embed nodes."

  (defn pure_ [self value]
    (frozenset))

  (defn lift_n_ [self f args]
    (.union (frozenset) #* args))

  (defn embed_ [self effect meta]
    (frozenset (.get meta "deps" (frozenset))))

  (defn bind_ [self inner-data cont]
    inner-data))
