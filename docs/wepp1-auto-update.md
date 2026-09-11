# Automatic updates on wepp1

Pushes to `main` run `.github/workflows/update-wepp1.yml`, which updates
`/geodata/extended_mods_data/wepppy-locations-portland` using
`git pull --ff-only origin main`. The same path is visible inside WEPPcloud
and RQ worker containers through their `/geodata` bind mount. No container
restart is performed, and existing run artifacts are not regenerated.

The workflow also supports manual dispatch from the Actions page on `main`.
Other branches and pull requests do not trigger this workflow. Keep this
production runner limited to the update workflow; do not route pull-request
jobs or untrusted code to it.

## Runner and service

- Repository runner: `wepp1-portland-data`, with custom label `wepp1-portland-data`.
- Installation: `/home/roger/actions-runner-portland`.
- Identity: `roger`, the existing production checkout owner.
- User service: `wepp1-portland-runner.service`.
- Unit: `/home/roger/.config/systemd/user/wepp1-portland-runner.service`.
- User lingering is enabled, so the service runs after logout and starts at boot.
- Initial runner version: 2.337.0; normal runner automatic updates are enabled.

Run these commands as `roger` on wepp1:

```bash
systemctl --user status wepp1-portland-runner.service
journalctl --user -u wepp1-portland-runner.service -n 100 --no-pager
systemctl --user restart wepp1-portland-runner.service
```

GitHub Actions logs and the job summary record the previous and deployed
commit. Runner diagnostic logs are under the installation's `_diag` directory.

## Update and recovery contract

Updates are serialized and hold `.git/wepp1-update.lock` using `flock`.
Preparation verifies the hostname, remote URL, branch, and clean working tree.
Local changes or divergent history cause an explicit failure; the workflow
never resets, cleans, stashes, or force-updates the checkout. A successful job
verifies that the triggering commit is an ancestor of the deployed HEAD;
newer pushes can already be included when queued jobs start.

If an update fails, inspect the Actions log and resolve the reported issue
before rerunning the job. Data changes become visible through the shared
mount immediately; coordinate changes with model execution as needed because
a Git pull is not an atomic replacement of the entire dataset.

To suspend automatic updates, disable the workflow in GitHub Actions. To stop
the runner persistently:

```bash
systemctl --user disable --now wepp1-portland-runner.service
```

For a data rollback, revert the unwanted commit on `main` and push the revert.
Avoid local production edits, which intentionally block subsequent updates.

This setup retains the existing checkout owner and mount layout. It uses a
user service because the existing user manager has lingering enabled, avoiding
a new runtime account or changes to production data permissions.
