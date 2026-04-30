;;; registry.hy — global algebra registry + defprim / defask declarative macros.
;;;
;;; Active algebras are mutated when a (defprim name ...) or (defask key ...)
;;; declaration is compiled. Each algebra's register-prim / register-ask hook
;;; cherry-picks the kwargs it cares about (e.g., CostAlgebra picks :cost).
;;;
;;; Pattern: declare your algebras once, register them globally, then write
;;; defprim / defask declarations anywhere. New analyses are added by
;;; defining a new Algebra class and registering it — no core change.

(setv *active-algebras* [])

(defn register-algebra [alg]
  "Add alg to the global active-algebras list. Returns alg."
  (.append *active-algebras* alg)
  alg)

(defn unregister-algebra [alg]
  (when (in alg *active-algebras*)
    (.remove *active-algebras* alg)))

(defn clear-registry []
  "Forget all registered algebras. Useful for tests."
  (.clear *active-algebras*))

(defn get-active-algebras []
  (list *active-algebras*))

(defn _register-prim [name #** kwargs]
  "Invoke register-prim on every active algebra."
  (for [alg *active-algebras*]
    (.register-prim alg name #** kwargs)))

(defn _register-ask [key #** kwargs]
  (for [alg *active-algebras*]
    (.register-ask alg key #** kwargs)))

(defmacro defprim [name #* rest]
  "Declare a primitive. All :keyword value pairs are forwarded to each
   active algebra's register-prim hook.

   (defprim fetch-news :cost 100 :type DataFrame :provenance \"polygon-v2\")"
  `(prism.registry._register-prim ~(str name) ~@rest))

(defmacro defask [key #* rest]
  "Declare an Ask key. Same kwargs forwarding as defprim.

   (defask threshold :type Float :default 0.5 :cost 0)"
  `(prism.registry._register-ask ~(str key) ~@rest))
