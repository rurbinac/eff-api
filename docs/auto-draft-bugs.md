# Auto-Draft Bug Fixes

**Fixed in commit `40e44ee`** — deployed as `eff-api-00177-pq8`

---

## Bug 1 — Stale `draftingUsers` caused zero auto-picks

### Files
- `app/actions/draft/draft_values.py` — added `reload_drafting_users()`
- `app/actions/draft/draft_helper.py` — call it before the auto-draft loop

### Symptom
`StartDraft` / `RestartDraft` returned 200 OK but fired no auto-picks for absent teams. `draftingTeamOrder` stayed at 1 in the DB.

### Root Cause
`get_drafting_users()` reads from `self._division["draftingUsers"]`, which is loaded once when the request starts (via `load_division()`). The cached value could be stale in two ways:

1. **Prior session data** — if all 10 teams had been online in a previous draft and some `member_removed` Pusher webhooks were missed, their user IDs remained in `draftingUsers`. When `RestartDraft` ran, `drafting_users` contained all 10 user IDs. The first absent team (draftOrder=1) had its `userID` in the list → `user_id in drafting_users` was `True` → `_draft_unsigned_users` returned `False` immediately → loop ran 0 times.

2. **Webhook timing** — Pusher `member_added` webhooks arrive asynchronously. If the signed-in user's webhook updated the DB *after* the division was loaded, `get_drafting_users()` still saw the old value.

### PHP Behaviour (reference)
PHP's `DraftingUsersHelper::teamIDNotIn()` does a **fresh `SELECT` from the DB** on every call. Python was reading a cached dict.

### Fix
Added `reload_drafting_users()` to `DraftValues`. It queries `draftingUsers` directly from the DB and refreshes the in-memory division dict. Called once in `_finish_process()` right before the auto-draft loop:

```python
self.draft_values.reload_drafting_users()
drafting_users = self._draft_values.get_drafting_users()
while self._draft_unsigned_users(team, drafting_users):
    ...
```

---

## Bug 2 — `dtm.is_valid` prevented any pick for teams with few members

### File
- `app/actions/draft/draft_member.py` — `DraftMember._process_ready()`

### Symptom
Auto-draft for teams with 0–14 members raised `NotAvailableMembersException` → 422 response. In round 1 every absent team has 0 members, so no auto-picks could ever be made.

### Root Cause
`_process_ready()` iterated candidate keys and checked `dtm.is_valid` after each `dtm.append(key)`:

```python
for key in self._next_member_key(available_positions):
    dtm.append(key)
    if dtm.is_valid:          # requires full team: no deficit AND no surplus
        self._selected_key = key
        dv.set_member_team_id(key, ...)
        return
raise NotAvailableMembersException()
```

`DraftingKeys.is_valid` means **the whole team has no deficit and no surplus** — i.e., all position minimums are met and none exceed their maximum. That is never true after adding a single pick to an empty team (which needs at least 16 members: 2 GK + 5 DEF + 5 MID + 2 STR + 2 EPL).

The loop accumulated keys into `dtm` without resetting. Once any capped position exceeded its maximum (e.g., a 3rd goalkeeper when `MAX_GK = 2`), `surplus` became `True` and `is_valid` could never recover. The loop exhausted all ~520 available members and raised `NotAvailableMembersException`.

### Fix
Removed `dtm.append(key)` and the `is_valid` check entirely. `available_dp()` already guarantees every yielded key fits the team's current position needs — the first key is always the correct pick:

```python
for key in self._next_member_key(available_positions):
    self._selected_key = key
    dv.set_member_team_id(key, team.get("teamID"), freeze_values=True)
    return
raise NotAvailableMembersException()
```

`dtm` is still used to compute `available_positions = dtm.available_dp(draft_lowest=True)`, which drives which positions the team accepts next.

---

## Position limits reference

| Position   | min | max | lowest |
|------------|-----|-----|--------|
| Goalkeeper |   2 |   2 |      1 |
| Defender   |   5 |   7 |      4 |
| Midfielder |   5 |   7 |      4 |
| Striker    |   2 |   3 |      2 |
| EPL Team   |   2 |   2 |      1 |
| **Total**  |  16 |  19 |      — |
