# Security Fixes — TODO

Alle Fixes wurden auf `code-review` Branch mit TDD (Test-First) und Commit umgesetzt.

---

## ✅ 1. Open Redirect via `request.referrer` (CRITICAL)

**File:** `app/routes/enrollment.py` (16 Vorkommen)

**Problem:** `request.referrer` kann von Angreifern kontrolliert werden → Phishing-Redirect.

**Fix:** Safe redirect utility in `app/utils/redirect.py`, alle Vorkommen ersetzt.

**Commit:** `f089808` — `fix: replace request.referrer with safe_redirect utility to prevent open redirects`

---

## ✅ 2. Unbound `tmp_path` Bug (CRITICAL)

**File:** `app/routes/document.py` (2 Stellen)

**Problem:** `tmp_path` wird nur innerhalb von `with tempfile.NamedTemporaryFile` zugewiesen. Wenn der Block fehlschlägt, ist `tmp_path` im `finally` ungebunden → `UnboundLocalError`.

**Fix:** `tmp_path = None` vor dem `with` Block initialisiert.

**Commit:** `7076f51` — `fix: initialize tmp_path to None before with block to prevent UnboundLocalError`

---

## ✅ 3. IDOR in Bulk-Grade Endpoint (CRITICAL)

**File:** `app/routes/grade.py` (Zeile 293-318)

**Problem:** `enrollment_id` kommt aus Form-Key (`points_<id>`), nicht validiert gegen die Prüfung. Jeder kann Noten für andere Prüfungen manipulieren.

**Fix:** Nur Enrollments der ausgewählten Prüfung werden akzeptiert. Form-Key wird ignoriert, stattdessen werden echte Enrollments der Prüfung durchlaufen.

**Commit:** `75999f3` — `fix: validate enrollment ownership in bulk grade endpoint to prevent IDOR`

---

## ✅ 4. Timing-Attacke auf API Key (CRITICAL)

**File:** `app/routes/api.py` (Zeile 47)

**Problem:** `request.headers.get("X-API-Key") != key` verwendet linearen String-Vergleich — angreifbar via Timing-Attack.

**Fix:** `secrets.compare_digest()` statt `!=` verwendet.

**Commit:** `172f475` — `fix: resolve 6 remaining security issues (audit, 405, datetime, boolean, load_user, coverage)`

---

## ✅ 5. Audit Service Auto-Commit (HIGH)

**File:** `app/services/audit_service.py` (Zeile 59-60)

**Problem:** `AuditService.log()` rief `db.session.commit()` auf. Wenn die Haupttransaktion rollbackt, bleibt der Audit-Eintrag erhalten (orphaned).

**Fix:** `commit()` entfernt, Audit-Eintrag wird nur hinzugefügt — der Aufrufer commitet.

**Commit:** `172f475` — `fix: resolve 6 remaining security issues (audit, 405, datetime, boolean, load_user, coverage)`

---

## ✅ 6. Missing 405 Handler (MEDIUM)

**File:** `app/__init__.py`

**Problem:** Kein 405 (Method Not Allowed) Error Handler. Flask gibt standardmäßige Antwort zurück.

**Fix:** 405 Error Handler hinzugefügt, Template erstellt.

**Commit:** `172f475`

---

## ✅ 7. Naive DateTime in PageAnnotation (MEDIUM)

**File:** `app/models/page_annotation.py` (Zeile 32-34)

**Problem:** `datetime.utcnow()` returns naive datetime, während andere Modelle `datetime.now(UTC)` verwenden.

**Fix:** `datetime.now(UTC)` statt `datetime.utcnow()`.

**Commit:** `172f475`

---

## ✅ 8. `== True` / `== False` Anti-Pattern (MEDIUM)

**File:** `app/routes/grade.py` (8 Vorkommen)

**Problem:** `Grade.is_final == True` ist ein Anti-Pattern, wird von Ruff E712 flaggt.

**Fix:** `is_(True)` statt `== True` verwendet. noqa-Kommentare entfernt.

**Commit:** `172f475`

---

## ✅ 9. load_user ohne Try/Catch (MEDIUM)

**File:** `app/__init__.py` (Zeile 64-68)

**Problem:** `int(user_id)` ohne Try/Catch → Crash bei malformed Flask-Login session cookie.

**Fix:** Try/Block um `int(user_id)`, gibt `None` bei InvalidUserError zurück.

**Commit:** `172f475`

---

## ✅ 10. Test Coverage Threshold (LOW)

**File:** `pyproject.toml` (Zeile 126)

**Problem:** Test Coverage Threshold bei 40% — zu niedrig.

**Fix:** Auf 50% erhöht.

**Commit:** `172f475`

---

## Zusammenfassung

| # | Issue | Severity | Status | Commit |
|---|-------|----------|--------|--------|
| 1 | Open Redirect | CRITICAL | ✅ Fixed | `f089808` |
| 2 | Unbound tmp_path | CRITICAL | ✅ Fixed | `7076f51` |
| 3 | IDOR Bulk Grade | CRITICAL | ✅ Fixed | `75999f3` |
| 4 | Timing Attack API Key | CRITICAL | ✅ Fixed | `172f475` |
| 5 | Audit Auto-Commit | HIGH | ✅ Fixed | `172f475` |
| 6 | Missing 405 Handler | MEDIUM | ✅ Fixed | `172f475` |
| 7 | Naive DateTime | MEDIUM | ✅ Fixed | `172f475` |
| 8 | == True Anti-Pattern | MEDIUM | ✅ Fixed | `172f475` |
| 9 | load_user Crash | MEDIUM | ✅ Fixed | `172f475` |
| 10 | Coverage Threshold | LOW | ✅ Fixed | `172f475` |
