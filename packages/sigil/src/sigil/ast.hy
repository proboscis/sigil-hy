;;; ast.hy — Free Applicative over Free Monad AST.
;;;
;;; The four node constructors are pure data — they carry no semantics.
;;; Applicative and monad implementations live in Algebra classes.
;;;
;;;   Pure   : value
;;;   Lift   : pure n-ary function applied to AST args (Applicative)
;;;   Bind   : monadic escape — inner AST + opaque continuation (Monad)
;;;   Embed  : leaf wrapper around an arbitrary user-domain value, plus a
;;;            meta dict that algebras read for analysis-specific
;;;            annotations (cost / type / deps / provenance / impl / ...).
;;;
;;; "Embed" carries NO algebraic-effects semantics by itself — it is the
;;; Free-Monad embedding constructor (literature names: Embed / Inj). The
;;; choice of what lives inside Embed (AskEff, PrimEff, FetchPrice, ...) is
;;; the user's domain decision.
;;;
;;; The `meta` dict is how applicative annotations travel with the AST —
;;; sigil has NO global registry, NO runtime state. Macros like defprim /
;;; defask are pure data factories that bake meta into every Embed node
;;; they construct, so each AST is fully self-describing. Analysis
;;; algebras read directly from meta and do NOT dispatch on the leaf
;;; type — that would be privileging some leaves over others.

(import dataclasses [dataclass])

(defclass [(dataclass :frozen True)] Pure []
  (annotate value object))

(defclass [(dataclass :frozen True)] Lift []
  (annotate f object)
  (annotate args tuple))

(defclass [(dataclass :frozen True)] Bind []
  (annotate inner object)
  (annotate cont object))

(defclass [(dataclass :frozen True)] Embed []
  (annotate effect object)
  (annotate meta dict))

(defn is-node [x]
  (or (isinstance x Pure)
      (isinstance x Lift)
      (isinstance x Bind)
      (isinstance x Embed)))
