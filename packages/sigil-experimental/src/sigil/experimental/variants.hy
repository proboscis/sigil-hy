;;; variants.hy — example defapmk variants built on the primitive defapmk.
;;;
;;; These macros are NOT part of the core abstraction. They demonstrate how
;;; users / library authors layer their own static-check syntax on top of
;;; the applicative-agnostic primitive.
;;;
;;; Pattern for a new variant:
;;;   1. Use (extract-clauses body) to split annotations from real body.
;;;   2. Walk the real body with (walk-body real-body).
;;;   3. Emit a function that constructs the AST and runs whatever Algebra
;;;      checks the variant cares about, then returns the AST.
;;;
;;; (require sigil.variants [defapmk-typed defapmk-checked])

(import sigil.macros [walk-body extract-clauses])
(import sigil.experimental.algebras.type_alg [TypeAlgebra])
(import sigil.interp [interp])


(defmacro defapmk-typed [name params #* body]
  "defapmk variant that runs TypeAlgebra check on every constructed AST.

   Optional :returns clause documents (and is currently advisory; future
   versions may assert the AST's inferred type matches it):

     (defapmk-typed score [#^ Float data]
       :returns Float
       (lift-n * data threshold))

   On every (score x) call, the AST is built and immediately walked by
   TypeAlgebra. lift-n type mismatches raise TypeError at the call site."
  (when (= (len body) 0)
    (raise (SyntaxError f"defapmk-typed {name}: body required")))
  (setv #(clauses real-body) (extract-clauses body))
  (when (= (len real-body) 0)
    (raise (SyntaxError f"defapmk-typed {name}: body required after clauses")))
  `(do
     (import sigil.interp                  [interp :as _apm-interp])
     (import sigil.experimental.algebras.type_alg [TypeAlgebra :as _ApmTypeAlgebra])
     (defn ~name ~params
       (setv _ast (do ~@(walk-body real-body)))
       (_apm-interp (_ApmTypeAlgebra) _ast)
       _ast)))


(defmacro defapmk-checked [name params #* body]
  "defapmk variant that runs an arbitrary list of Algebra checks on every
   constructed AST. The :check clause is required and must be a list of
   Algebra instances:

     (defapmk-checked strategy [data]
       :check [(TypeAlgebra) (CostAlgebra :default-prim 1.0)]
       (lift-n * data threshold))

   Each algebra is interpreted; any TypeError / ValueError raised inside
   propagates to the caller."
  (when (= (len body) 0)
    (raise (SyntaxError f"defapmk-checked {name}: body required")))
  (setv #(clauses real-body) (extract-clauses body))
  (when (not (in "check" clauses))
    (raise (SyntaxError f"defapmk-checked {name}: :check clause is required")))
  (setv checks (get clauses "check"))
  `(do
     (import sigil.interp [interp :as _apm-interp])
     (defn ~name ~params
       (setv _ast (do ~@(walk-body real-body)))
       (for [_alg ~checks] (_apm-interp _alg _ast))
       _ast)))
