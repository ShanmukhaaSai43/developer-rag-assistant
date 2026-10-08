# Deployment & Prompt Versioning Plan — Week 11 Task Set B

## 1. Prompt Version Bump Record

- **Previous Version**: `v1.0.0` (Incident baseline — flawed RAG chunk chunk `ctx_ghee_notes_088` allowed Ghee as dairy-free)
- **New Bumped Version**: `v1.1.0` (Fixed production release — strictly enforces allergen boundaries, bans ghee/butterfat/casein for dairy-free requests)
- **Root Cause & Fix Summary**: Added strict negative allergen constraints in the prompt layer and implemented metadata tag filtering on vector store chunks to exclude dairy-derived fats when `input_type == dairy_free`.

---

## 2. Two-Line Canary Deployment Plan

```text
CANARY PLAN: Route 5% of production traffic to prompt v1.1.0 for 30 minutes while automated real-time telemetry filters for allergen assertion flags.
GRADUAL ROLLOUT: If zero allergen flags and error rate stays < 0.01%, scale traffic linearly (5% -> 25% -> 100%) over 2 hours while monitoring trace spans.
```

---

## 3. Two-Line Rollback Plan

```text
ROLLBACK TRIGGER: If telemetry detects any allergen violation or evaluation assertion failure in production traces, instantly revert feature-flag 'PROMPT_VERSION' to v1.0.0 via instant edge config update.
INCIDENT POST-MORTEM: Lock v1.1.0 deployment, preserve failing trace logs in production.log, and escalate to safety review squad before re-attempting rollout.
```

---

## 4. Evaluation Suite Verification Summary

| Prompt Version | Total Cases | Pass Count | Pass Rate | Suite Health State |
|---|---|---|---|---|
| `v1.0.0` (Baseline) | 10 | 9 / 10 | 90.0% | **RED** (Failed `eval_010_dairy_free_ghee`) |
| `v1.1.0` (Fixed Release) | 10 | 10 / 10 | 100.0% | **GREEN** (All cases passed) |
