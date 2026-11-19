# Publish a Roundframe for CS2 release

The public repository is [abhiraj109/cs2-roundframe](https://github.com/abhiraj109/cs2-roundframe). The project uses the [MIT License](../LICENSE). Review [third-party notices](THIRD_PARTY.md) before distributing the Leetify attribution artwork.

## Prepare a new version

1. Update `VERSION` and `CHANGELOG.md` for the new release. Run the checks in [CONTRIBUTING.md](../CONTRIBUTING.md), then build the Windows ZIP:

   ```powershell
   python scripts/build_release.py
   ```

   The archive is named `dist/cs2-roundframe-<version>-windows.zip`. Extract it to a clean folder, verify the archive contents, and smoke-test setup, launch, OBS preview and uninstall. Record its SHA-256 checksum.

2. Review the files being published and the Git author identity before committing. Never stage local settings, match history, API keys or generated runtime data.

   ```powershell
   git status --short --ignored
   git diff --check
   git diff --stat
   git diff --name-only
   gitleaks git --redact --log-opts="--all"
   ```

3. Commit and push the tested change to `main`. Wait for all GitHub Actions checks, including the secret scan, to pass.

4. Create a GitHub release for the new version tag, attach the matching Windows ZIP, and add the checksum and summary to the release notes. Verify the published download before announcing it. See [GitHub release instructions](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository).

The existing `v4.1.0` release was published before the rename and keeps its original asset name and URL. Leave that release intact; a rename does not require republishing it. New builds use the Roundframe archive name.
