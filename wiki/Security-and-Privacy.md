<h1>Security & Privacy</h1>


EDMRN is designed to keep commander data local.

<h2>What EDMRN Does</h2>

* Reads Elite Dangerous journal files locally
* Reads the journal in read-only fashion
* Saves route information locally
* Creates the in-game overlay
* Copies system names to the clipboard when requested
* Checks GitHub for application version updates
* Uses Spansh / EDSM / EDAstro APIs for supported features

<h2>What EDMRN Does Not Do</h2>

*  No telemetry collection
*  No analytics collection
*  No personal information harvesting
*  No game memory manipulation
*  No DLL injection
*  No automated keyboard or mouse input
*  No third-party data sharing
*  No online account required
*  No background process remains after the application is closed

<h2>Local Data</h2>

EDMRN stores data locally in:

```text
%USERPROFILE%\Documents\EDMRN_Route_Data\
```

Including:

```text
EDMRN_Route_Data\
|--- backups\
|--- logs\
`--- settings.json
```

There is no cloud storage for EDMRN route data.

**Your route data stays on your PC.**

---
