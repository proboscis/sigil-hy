;;; ast.hy — Free Applicative over Free Monad AST.
;;;
;;; The four node constructors are pure data — they carry no semantics.
;;; Applicative and monad implementations live in Algebra classes.
;;;
;;;   Pure  : value
;;;   Lift  : pure n-ary function applied to AST args (Applicative)
;;;   Bind  : monadic escape — inner AST + opaque continuation (Monad)
;;;   Eff   : leaf wrapper around an arbitrary user-domain value
;;;
;;; "Eff" carries NO algebraic-effects semantics by itself — it is the
;;; Free-Monad embedding constructor (literature names: Embed / Inj). The
;;; choice of what lives inside Eff (AskEff, PrimEff, FetchPrice, ...) is
;;; the user's domain decision. Algebras dispatch on the type of node.value.
;;;
;;; Pure | Lift | Eff = the Applicative-only sub-tree (statically analyzable
;;; to the leaf). Bind caps analysis: cont is value-dependent and opaque.

(import dataclasses [dataclass])

(defclass [(dataclass :frozen True)] Pure []
  (annotate value object))

(defclass [(dataclass :frozen True)] Lift []
  (annotate f object)               ; pure n-ary function
  (annotate args tuple))            ; tuple of AST nodes

(defclass [(dataclass :frozen True)] Bind []
  (annotate inner object)           ; AST node
  (annotate cont object))           ; Callable: value -> AST node (opaque)

(defclass [(dataclass :frozen True)] Eff []
  (annotate effect object))         ; first-class Effect dataclass

(defn is-node [x]
  (or (isinstance x Pure)
      (isinstance x Lift)
      (isinstance x Bind)
      (isinstance x Eff)))
