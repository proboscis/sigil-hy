;;; experimental/macros.hy — defprim / defask macros (pure data factories).
;;;
;;; No global state, no registry. These macros emit code that constructs
;;; Embed-laden AST nodes with per-leaf meta baked in at the declaration
;;; site. Analysis algebras read meta directly when interpreting Embed
;;; nodes — there is no out-of-band channel.

(import hy)
(import hy.models)


(defn _kwargs->meta-dict [rest]
  "Convert (:k1 v1 :k2 v2 ...) to a hy dict literal whose keys are
   plain strings (the keyword without the leading colon)."
  (setv flat [])
  (setv i 0)
  (while (< (+ i 1) (len rest))
    (setv k (get rest i))
    (setv v (get rest (+ i 1)))
    (.append flat (hy.models.String (.lstrip (str k) ":")))
    (.append flat v)
    (setv i (+ i 2)))
  (hy.models.Dict flat))


(defmacro defprim [name #* rest]
  "Define a function that builds an Embed-laden AST node for a registered
   primitive. All :keyword value pairs are baked into the node's meta dict.

     (defprim fetch-news :cost 100 :type DataFrame :impl my-fetch-fn)
     (fetch-news \"BTC\")
     ; -> Embed(PrimEff('fetch-news', ('BTC',)),
     ;          {'cost': 100, 'type': DataFrame, 'impl': my-fetch-fn})"
  (setv name-str (str name))
  (setv meta-dict (_kwargs->meta-dict rest))
  `(do
     (import sigil.constructors [embed :as _sigil-embed])
     (import sigil.experimental.effects [PrimEff :as _SigilPrimEff])
     (defn ~name [#* args]
       (_sigil-embed (_SigilPrimEff ~name-str (tuple args)) :meta ~meta-dict))))


(defmacro defask [key #* rest]
  "Define a constant Embed-laden AST node for an Ask key. Baked-in meta
   includes the user-supplied annotations PLUS deps={key} so DepsAlgebra
   sees the dependency without dispatching on the leaf type.

     (defask threshold :type Float :default 0.5)
     threshold
     ; -> Embed(AskEff('threshold'),
     ;          {'type': Float, 'default': 0.5, 'deps': frozenset({'threshold'})})"
  (setv key-str (str key))
  (setv meta-dict (_kwargs->meta-dict rest))
  `(do
     (import sigil.constructors [embed :as _sigil-embed])
     (import sigil.experimental.effects [AskEff :as _SigilAskEff])
     (setv ~key
           (_sigil-embed (_SigilAskEff ~key-str)
                         :meta (| ~meta-dict
                                  {"deps" (frozenset [~key-str])})))))
