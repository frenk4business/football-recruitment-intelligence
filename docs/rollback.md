# Rollback runbook

Known-good pre-v1 target: commit `29beb4d4462dda37b6ec0abca82ac904cef9620d`, Render deployment `dep-daul9fo473hc739ojjlg` (live before Phase 5). Service `srv-dauh12hsrm7s73c7uiu0`; [Dashboard](https://dashboard.render.com/static/srv-dauh12hsrm7s73c7uiu0). No database migrations exist.

1. Record the incident, current main SHA, live deploy SHA/ID, failing routes and release-manifest version. Do not include personal data or secrets in logs/issues.
2. For an urgent outage, disable automatic deployment temporarily and use the Render Events menu to roll back to the known-good deployment. If that deployment is no longer retained, manually deploy the target commit from the same repository with `render deploys create srv-dauh12hsrm7s73c7uiu0 --commit 29beb4d4462dda37b6ec0abca82ac904cef9620d --wait --confirm`. Confirm CLI support/account authorization first. This changes the live site; document the temporary main/live mismatch.
3. Revert the faulty change on a new branch, open a PR, run CI and merge the revert to main. For a merge commit use `git revert -m 1 <bad-merge-sha>` after inspecting its parents; do not rewrite main history. Enable checked-main automatic deployment after the corrective main passes.
4. Roll back code and committed artifacts together. Never mix an old UI with newly regenerated data. Release manifests bind each artifact to SHA-256; scientific lock prevents silent result changes. The pre-v1 target has no v1 release manifest, so verify its pinned Phase 4 manifest and known SHA instead.
5. Keep the security/cache headers unless they caused the incident. If a header was at fault, restore the recorded preceding rules via Dashboard/API and verify real responses. Do not remove HTTPS protections as a generic repair. Settings are separate from a code deploy.
6. Run the production browser smoke workflow on all three engines, check EN/NL routes/404/console/data hashes and current main==live SHA. Announce resolution in the issue; issue a PATCH release if appropriate. Never move an existing version tag to hide the incident.

This is a documented, read-only-reviewed procedure, not a claim that a disruptive live rollback drill was performed. Retention of historical Render deploys is provider/account dependent; retaining Git tags and release manifests provides the rebuild fallback.
