;;; sigil.macros — defapm / defapmk for the apm DSL.
;;;
;;; Usage:
;;;   (require sigil.macros [defapm defapmk])
;;;   (import sigil [pure apm-ask apm-list apm-dict
;;;                                  apm-tuple apm-set lift-n run-apm])
;;;
;;; Body walker (applied recursively to every value position):
;;;   - Numeric / String / Bytes literal -> (pure literal)
;;;   - Bool / None (Hy parses as Symbol) -> (pure literal)
;;;   - List literal  [a b c]   -> (apm-list <a> <b> <c>)
;;;   - Dict literal  {:k v}    -> (apm-dict :k <v>)         ; keys not walked
;;;   - Tuple literal #(a b c)  -> (apm-tuple <a> <b> <c>)
;;;   - Set literal   #{a b}    -> (apm-set <a> <b>)
;;;   - Symbol / Keyword         -> as-is (apm reference or kwarg marker)
;;;   - Expression (call)        -> as-is (the call must return Apm)
;;;
;;; Important: the walker does NOT descend into Expressions. A function call
;;; like (apm-ask "x") is opaque — its arguments are passed through verbatim.
;;; This means raw literals are only auto-pure'd when they appear directly in
;;; a value position OR inside a structural literal — never inside another
;;; function call.

(import hy)
(import hy.models)

(defn _is-numeric-literal [form]
  (or (isinstance form hy.models.Integer)
      (isinstance form hy.models.Float)))

(defn _is-text-literal [form]
  (or (isinstance form hy.models.String)
      (isinstance form hy.models.Bytes)))

(defn _is-special-symbol-literal [form]
  "Hy parses True / False / None as Symbol — detect by string value."
  (and (isinstance form hy.models.Symbol)
       (in (str form) #{"True" "False" "None"})))

(defn _walk [form]
  "Walk a value-position form, returning a form that produces an Apm."
  (cond
    ;; numeric / string / bytes literal -> pure
    (or (_is-numeric-literal form) (_is-text-literal form))
    `(pure ~form)

    ;; True / False / None -> pure
    (_is-special-symbol-literal form)
    `(pure ~form)

    ;; list literal -> apm-list of walked items
    (isinstance form hy.models.List)
    `(apm-list ~@(lfor x form (_walk x)))

    ;; dict literal -> apm-dict of alternating k/v (keys not walked, values walked)
    (isinstance form hy.models.Dict)
    (do
      (setv flat [])
      (for [#(k v) (zip (cut form None None 2) (cut form 1 None 2))]
        (.append flat k)
        (.append flat (_walk v)))
      `(apm-dict ~@flat))

    ;; tuple literal -> apm-tuple
    (isinstance form hy.models.Tuple)
    `(apm-tuple ~@(lfor x form (_walk x)))

    ;; set literal -> apm-set
    (isinstance form hy.models.Set)
    `(apm-set ~@(lfor x form (_walk x)))

    ;; symbol / keyword / expression / anything else -> as-is
    True
    form))

;; ---------------------------------------------------------------------------
;; Public helpers — used by variant macros (defapmk-typed / defapmk-checked / etc.)
;; ---------------------------------------------------------------------------

(defn walk-body [forms]
  "Apply the literal / structural lift rules to every form in `forms`.
   Returns a list of walked forms. Use this from variant macros so all
   defapmk-* derivatives share identical body semantics."
  (lfor f forms (_walk f)))

(defn extract-clauses [body]
  "Pop leading :keyword value pairs from `body`. Returns #(clauses real-body)
   where clauses is a dict (keys are the keyword string without the leading ':')
   and real-body is whatever remains.

   Stops at the first form that is not a Keyword. Handy for variant macros
   that accept their own annotation clauses (e.g. :returns, :cost-cap)."
  (setv clauses {})
  (setv i 0)
  (while (and (< (+ i 1) (len body))
              (isinstance (get body i) hy.models.Keyword))
    (setv k (.lstrip (str (get body i)) ":"))
    (setv v (get body (+ i 1)))
    (setv (get clauses k) v)
    (setv i (+ i 2)))
  (setv real-body (cut body i None))
  #(clauses real-body))

;; ---------------------------------------------------------------------------
;; Public macros — primitives (applicative-agnostic)
;; ---------------------------------------------------------------------------

(defmacro defapm [name #* body]
  "Define an Apm constant.

  (defapm threshold (apm-ask \"threshold\"))

  The body is a single expression that must produce an Apm at runtime."
  (when (= (len body) 0)
    (raise (SyntaxError f"defapm {name}: body is required")))
  (when (> (len body) 1)
    (raise (SyntaxError f"defapm {name}: takes a single expression")))
  `(setv ~name ~(get body 0)))

(defmacro defapmk [name params #* body]
  "Define an Apm Kleisli function (args -> Apm).

  Body forms are walked: literals and structural forms are auto-lifted via
  pure / apm-list / apm-dict / apm-tuple / apm-set. Function calls (including
  apm-ask, lift-n, defapmk calls) are NOT descended into — pass apm or apm
  values to them explicitly.

  Examples:
    (defapmk score [data]
      (lift-n * data threshold))

    (defapmk pair [data]
      [(score data) (rank data)])      ;; -> apm[list]

    (defapmk config []
      {:thr threshold-apm :max 100})   ;; literal value 100 auto-pure'd"
  (when (= (len body) 0)
    (raise (SyntaxError f"defapmk {name}: body is required")))
  `(defn ~name ~params ~@(walk-body body)))
