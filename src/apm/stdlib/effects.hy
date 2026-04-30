;;; effects.hy — STANDARD LIBRARY of leaf types and their constructors.
;;;
;;; NOT core. These dataclasses + constructors are example domain types that
;;; the bundled algebras (Deps / Cost / Type / Execution / Identity)
;;; recognise. They are not intrinsic to the applicative + monad abstraction
;;; — users may define their own leaf types (e.g. FetchPrice, RunQuery) and
;;; either subclass these algebras or write fresh ones.
;;;
;;; Core is just (Pure | Lift | Bind | Eff) + the 4-method Algebra protocol.
;;; What goes inside Eff is a domain choice.

(import dataclasses [dataclass])
(import apm.constructors [eff])

;; ── Leaf dataclasses ─────────────────────────────────────────────

(defclass [(dataclass :frozen True)] Effect []
  "Optional base class, by convention. Not required — algebras dispatch on
   exact type rather than on this base.")

(defclass [(dataclass :frozen True)] AskEff [Effect]
  "Read a value from the env by key. Bridges to doeff Ask via
   ExecutionAlgebra; consumed by Deps / Cost / Type / Identity algebras."
  (annotate key str))

(defclass [(dataclass :frozen True)] PrimEff [Effect]
  "Call a registered pure primitive by name with literal args. Consumed by
   Cost / Type algebras (annotation lookup) and Execution / Identity
   (impl lookup)."
  (annotate name str)
  (annotate args tuple))

(defclass [(dataclass :frozen True)] DoeffEff [Effect]
  "Wraps an arbitrary doeff effect (Slog, Get, Put, Tell, Try, ...) so any
   doeff effect flows through the apm DSL. ExecutionAlgebra forwards the
   wrapped effect to doeff verbatim. Other algebras either ignore it
   (Deps / Cost return defaults) or raise (Identity has no doeff runtime)."
  (annotate effect object))

;; ── Convenience constructors (build on `eff`) ─────────────────────

(defn apm-ask [key]
  "Convenience: (eff (AskEff key))."
  (eff (AskEff key)))

(defn apm-prim [name #* args]
  "Convenience: (eff (PrimEff name (tuple args)))."
  (eff (PrimEff name (tuple args))))

(defn apm-doeff [doeff-effect]
  "Wrap any doeff effect (Slog/Get/Put/Tell/Try/...) as an apm leaf, so
   the full doeff effect set is available from apm DSL.

   Example:
     (import doeff-core-effects.effects [Slog])
     (apm-doeff (Slog \"starting\"))"
  (eff (DoeffEff doeff-effect)))
