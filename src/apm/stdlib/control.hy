;;; control.hy — control-flow combinators on top of bind.
;;;
;;; These are NOT core. They're convenience patterns built on `bind`. The
;;; structure each one produces is a Bind tree whose `cont` lazily yields
;;; the next AST step, so the AST does not grow upfront — the VM consumes
;;; Bind nodes one at a time (trampoline).

(import apm.constructors [pure bind])


(defn apm-when [cond-apm body-apm]
  "Run body-apm only if cond-apm yields truthy. Returns body's value or None."
  (bind cond-apm
        (fn [c] (if c body-apm (pure None)))))


(defn apm-if [cond-apm then-apm else-apm]
  "Conditional dispatch on a runtime apm value. Both branches must produce
   apm values; only one is reached at runtime."
  (bind cond-apm
        (fn [c] (if c then-apm else-apm))))


(defn apm-while [cond-apm body-apm]
  "Run body-apm while cond-apm yields truthy. Returns None when the loop
   exits. Built on bind + recursion; the cont lambda lazily produces the
   next AST step so the tree does not blow up."
  (bind cond-apm
        (fn [c]
          (if c
              (bind body-apm (fn [_] (apm-while cond-apm body-apm)))
              (pure None)))))


(defn apm-times [n body-apm]
  "Run body-apm n times. Implemented as a counted while loop without a
   doeff state effect — the count lives in the cont lambda's closure."
  (defn _loop [remaining]
    (if (<= remaining 0)
        (pure None)
        (bind body-apm (fn [_] (_loop (- remaining 1))))))
  (_loop n))
