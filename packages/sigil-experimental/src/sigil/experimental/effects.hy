;;; effects.hy — STANDARD LIBRARY of leaf types and their constructors.
;;;
;;; NOT core. These dataclasses + constructors are example domain types
;;; that the bundled algebras (Deps / Cost / Type / Execution / Identity)
;;; recognise via meta. They are not intrinsic to the applicative + monad
;;; abstraction — users may define their own leaf types and either bake
;;; their own meta keys or write fresh algebras.
;;;
;;; Core is just (Pure | Lift | Bind | Embed) + the 4-method Algebra
;;; protocol. What goes inside Embed and what is in `meta` are domain
;;; choices.

(import dataclasses [dataclass])
(import sigil.constructors [embed])

;; ── Leaf dataclasses ─────────────────────────────────────────────

(defclass [(dataclass :frozen True)] Effect []
  "Optional convention base. Algebras dispatch on leaf via meta keys,
   not on this class.")

(defclass [(dataclass :frozen True)] AskEff [Effect]
  (annotate key str))

(defclass [(dataclass :frozen True)] PrimEff [Effect]
  (annotate name str)
  (annotate args tuple))

(defclass [(dataclass :frozen True)] DoeffEff [Effect]
  (annotate effect object))

;; ── Convenience constructors ─────────────────────────────────────
;; Each constructor bakes the appropriate analysis-keys into meta so
;; algebras don't have to dispatch on the leaf type.

(defn ask [key]
  "(embed (AskEff key) :meta {'deps' #{key}}) — Ask-flavored leaf."
  (embed (AskEff key) :meta {"deps" (frozenset [key])}))

(defn prim [name #* args]
  "(embed (PrimEff name args)) — name-tagged primitive call."
  (embed (PrimEff name (tuple args))))

(defn doeff [doeff-effect]
  "(embed (DoeffEff effect)) — opaque doeff effect bridge.

   If the wrapped effect is a doeff Ask, also bake :deps so DepsAlgebra
   can see through. Other doeff effects stay opaque to analysis."
  (try
    (do
      (import doeff [Ask :as _DoeffAsk])
      (if (isinstance doeff-effect _DoeffAsk)
          (embed (DoeffEff doeff-effect)
                 :meta {"deps" (frozenset [doeff-effect.key])})
          (embed (DoeffEff doeff-effect))))
    (except [ImportError]
      (embed (DoeffEff doeff-effect)))))
