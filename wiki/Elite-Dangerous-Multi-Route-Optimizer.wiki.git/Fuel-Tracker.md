<h1>Real-Time Fuel Tracker</h1>

EDMRN includes real-time fuel monitoring.

<h3>Automatic detection</h3>

EDMRN can detect:

* Current fuel level from `Status.json`
* Ship fuel capacity from the journal `Loadout` event
* On-foot status
* Current CMDR information

<h3>Fuel display</h3>

Fuel is displayed in both the main application and the in-game overlay.

Example:

`Fuel: 85% (13.6/16.0t)`

When on foot:

`Fuel: On Foot`

<h3>Visual indicators</h3>

Fuel status uses configurable warning levels:

*  Above 50%
*  25-50%
*  15-25%
*  Below 15%

Fuel information is updated in real time.

<h3>Audio alerts</h3>

Configure:

* Warning threshold: 5-30%
* Critical threshold
* Sound enable/disable
* System volume

Audio alerts use WAV notifications with a cooldown to prevent repeated warnings.

---
