# publish_skill.py v2.3.2 Changes

## Date: 2026-05-14

### Changes

1. **Recursive skill directory lookup** (`find_skill_dir`)
   - Old: `Path.home() / '.hermes' / 'skills' / args.skill_name`
   - New: `Path.home() / '.hermes' / 'skills'.rglob(args.skill_name)`
   - Reason: Skills in category subdirectories (e.g., `productivity/skill-publisher`) were not found
   - Pitfall: If multiple matches exist, takes first one; use `--skill-dir` to disambiguate

2. **Fixed finally block deleting user work directories**
   - Old: `finally: shutil.rmtree(work_dir)` — deleted everything including user-specified dirs
   - New: Only deletes `/tmp/<skill>-push` directories; preserves `--work-dir` and `HERMES_WORK_DIR` dirs
   - Reason: User's `~/hermes-work/default/hermes-skills` was being wiped after each publish

3. **`HERMES_WORK_DIR` environment variable support**
   - Script reads `HERMES_WORK_DIR` from `~/.hermes/.env` as fallback when `--work-dir` not provided
   - Configured in INT step, eliminates need to pass `--work-dir` every time
   - Priority: `--work-dir` > `HERMES_WORK_DIR` > clone to `/tmp`

### Files Modified
- `~/.hermes/skills/productivity/skill-publisher/scripts/publish_skill.py` — lines 548-558 (directory lookup + finally fix)
