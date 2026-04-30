;;; constructors.hy — CORE AST constructors only.
;;;
;;; Leaf-agnostic; no AskEff / PrimEff knowledge. Users requiring those (or
;;; their own leaf types) build on `embed` directly. Standard-library leaf
;;; constructors live in sigil.effects (ask / prim).
;;;
;;;   pure     : value -> Apm
;;;   lift-n   : f, *Apm -> Apm           (n-ary applicative composition)
;;;   bind     : Apm, (a -> Apm) -> Apm   (monadic escape)
;;;   embed      : value -> Apm             (generic Free-Monad embed)
;;;
;;; Pure-applicative sugar for collection literals (no leaf types involved):
;;;   list-of / tuple-of / set-of / dict-of

(import sigil.ast [Pure Lift Bind Embed])

;; ── Core (applicative + monad, leaf-agnostic) ────────────────────

(defn pure [value]
  "Lift a plain value into the AST."
  (Pure value))

(defn lift-n [f #* args]
  "Apply pure n-ary function f to AST args (Applicative composition)."
  (Lift f (tuple args)))

(defn bind [inner cont]
  "Monadic escape: run inner, feed value into cont, run cont's AST.
   cont is opaque — Applicative analyses cap below this node."
  (Bind inner cont))

(defn embed [value]
  "Wrap an arbitrary user-domain value as an AST leaf. This is the generic
   Free-Monad embedding constructor — `Embed` carries no effect semantics by
   itself; algebras decide what to do based on type(value).

   For example, users may define their own leaf type:
     (defclass [(dataclass :frozen True)] FetchPrice []
       (annotate symbol str))
     (embed (FetchPrice \"BTC\"))   ; → Embed(FetchPrice('BTC'))"
  (Embed value))

(defn list-of [#* items]
  "AST node that, when interpreted, yields list of item values."
  (Lift (fn [#* xs] (list xs)) (tuple items)))

(defn tuple-of [#* items]
  (Lift (fn [#* xs] (tuple xs)) (tuple items)))

(defn set-of [#* items]
  (Lift (fn [#* xs] (frozenset xs)) (tuple items)))

(defn dict-of [#* kv]
  "dict-of k1 v1 k2 v2 ...  — keys are values (typically literals)."
  (when (% (len kv) 2)
    (raise (ValueError "dict-of requires alternating key/value pairs")))
  (setv ks (tuple (cut kv None None 2)))
  (setv vs (tuple (cut kv 1 None 2)))
  (Lift (fn [#* values] (dict (zip ks values))) vs))
