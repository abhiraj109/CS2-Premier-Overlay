# Troubleshooting

| Symptom | Check |
| --- | --- |
| Overlay missing or Browser Source blank | Start `run_overlay.bat`, then open `http://127.0.0.1:3000/?demo=1` in your browser. If the browser works, check OBS source visibility, ordering and URL. Keep **Local file** off and use **Refresh cache of current page** in Browser Source properties. |
| Python is unrecognized | Install Python 3.10 or newer with the launcher or PATH option. Reopen Command Prompt and check `py -3 --version` or `python --version`. |
| Port 3000 is busy | If another overlay instance is running, stop it. In PowerShell, `Get-NetTCPConnection -LocalPort 3000 -State Listen` lists the owning PID. Identify the owner with `Get-Process -Id <PID>` and close or reconfigure that app through its normal controls. |
| GSI never connects | Rerun `install_gsi.bat` or copy the config manually as described in the [installation guide](INSTALLATION.md). Fully restart CS2 and join a match. `/api/health` shows the age of the latest real packet. The sample GSI endpoint has its own independent state. |
| Steam account missing or incorrect | Sign in to the Steam desktop client, then open local Settings. Wait for the active account to update or save a SteamID64 override. Clear the override when switching back to automatic detection. |
| Leetify profile unavailable | Verify public visibility and that the profile matches the selected Steam account. HTTP 401 suggests checking the optional key. For HTTP 429, allow the retry timer to pass. Restart the overlay after changing the Windows user environment variable. |
| Premier Rating is blank | Check that the profile has a current CS Rating and the provider is enabled. Leetify needs time to process matches. The offline mode and local GSI history leave this field blank. |
| Historical data is stale | Check the update/status label and allow the refresh interval. Confirm that the provider has processed your latest match. For local history the server has to see live play and a terminal packet with both scores for your account. Run the overlay before joining. |
| Overlay is too small, stretched, or cut off | Set the source viewport to 640 × 180, reset the OBS transform, clear crop and any custom CSS, then apply a uniform scene scale. OBS editor zoom only changes the view of the canvas. [OBS scaling reference](https://obsproject.com/kb/aspect-ratio-guide) |
| Stop script fails or server stays open | Run `stop_overlay.bat` from the correct project copy. Press **Ctrl+C** in the actual overlay window if the stop request fails. If Windows sign-in starts it again, run `remove_startup.bat`. |
