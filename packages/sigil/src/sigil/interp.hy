;;; interp.hy — generic AST → Algebra interpretation.
;;;
;;; (interp alg ast) folds the AST through an Algebra. Pure / Lift / Eff are
;;; dispatched to alg.pure_ / alg.lift_n_ / alg.eff_; Bind threads inner's
;;; result through alg.bind_ along with the (still opaque) continuation.

(import sigil.ast [Pure Lift Bind Eff])

(defn interp [alg ast]
  "Fold ast through alg. Returns whatever alg's carrier type is."
  (cond
    (isinstance ast Pure)
    (.pure_ alg ast.value)

    (isinstance ast Lift)
    (.lift_n_ alg ast.f
              (tuple (gfor a ast.args (interp alg a))))

    (isinstance ast Eff)
    (.eff_ alg ast.effect)

    (isinstance ast Bind)
    (.bind_ alg (interp alg ast.inner) ast.cont)

    True
    (raise (TypeError f"interp: not an AST node: {ast}"))))
