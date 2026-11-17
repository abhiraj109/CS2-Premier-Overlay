# Publish the project on GitHub

The local branch is `main`. The project uses the [MIT License](../LICENSE). Resolve the [Leetify terms review](THIRD_PARTY.md) before publishing the current integration.

1. Run the checks in [CONTRIBUTING.md](../CONTRIBUTING.md) and build with `python scripts/build_release.py`. Extract and smoke-test the final ZIP. Record its SHA-256. Review the final source and asset permissions, including the provider attribution mark and copyright for contributed code.
2. Stage the reviewed source, then inspect its contents and run a redacted secret scan. Confirm the Git author email is one you want published. GitHub offers a [noreply email configuration](https://docs.github.com/en/account-and-profile/how-tos/email-preferences/setting-your-commit-email-address).

   ```powershell
   git status --short --ignored
   git add --all
   git diff --cached --check
   git diff --cached --stat
   git diff --cached --name-only
   gitleaks git --staged --redact
   git commit -m "Prepare CS2 Premier Sync for public release"
   gitleaks git --redact --log-opts="--all"
   ```

3. On GitHub create an empty public repository named **CS2-Premier-Overlay**. Leave GitHub's README, ignore file, and license initialization unchecked. Suggested description is “A lightweight CS2 Premier statistics overlay for OBS Studio with live GSI, Premier Rating and recent matchmaking history.” Set topics to `counter-strike-2`, `cs2`, `obs-studio`, `obs-overlay`, `game-state-integration`, `premier-rating`, `python`, and `open-source`. [GitHub repository setup](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository)
4. Use the owner from the new GitHub URL in these commands.

   ```powershell
   git remote add origin https://github.com/OWNER/CS2-Premier-Overlay.git
   git push -u origin main
   ```

5. Verify the public README, preview image, license and Actions run. Enable [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/working-with-repository-security-advisories/configuring-private-vulnerability-reporting-for-a-repository) and make a private conduct-report contact available.
6. After CI passes, open **Releases → Draft a new release**. Choose `v4.1.0` on the tested commit, use [release notes](RELEASE_NOTES.md) and attach `dist/CS2-Premier-Overlay-4.1.0-windows.zip`. Add the checksum to the notes, check the download, then publish. [GitHub release instructions](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
