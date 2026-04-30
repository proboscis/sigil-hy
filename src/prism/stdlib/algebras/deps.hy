;;; algebras/deps.hy — DepsAlgebra: collect AskEff keys (DepsA Applicative).

(import prism.stdlib.effects [AskEff PrimEff DoeffEff])


(defclass DepsAlgebra []
  "Collect Ask keys reachable through Pure/Lift/Eff. Bind caps analysis."

  (defn pure_ [self value]
    (frozenset))

  (defn lift_n_ [self f args]
    (.union (frozenset) #* args))

  (defn eff_ [self effect]
    (cond
      (isinstance effect AskEff)  (frozenset [effect.key])
      (isinstance effect PrimEff) (frozenset)
      (isinstance effect DoeffEff)
      ;; If the wrapped doeff effect is itself an Ask, surface its key;
      ;; otherwise opaque (no Ask deps from arbitrary doeff effects).
      (do
        (import doeff [Ask :as _DoeffAsk])
        (if (isinstance effect.effect _DoeffAsk)
            (frozenset [effect.effect.key])
            (frozenset)))
      True (raise (TypeError f"DepsAlgebra: unknown effect {(type effect)}"))))

  (defn bind_ [self inner-data cont]
    inner-data)

  (defn register-prim [self name #** kwargs] None)
  (defn register-ask  [self key  #** kwargs] None))
