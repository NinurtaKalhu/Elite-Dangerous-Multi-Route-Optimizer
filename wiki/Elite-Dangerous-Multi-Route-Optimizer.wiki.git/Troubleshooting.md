# Troubleshooting

## Antivirus False Positives

Some antivirus programs may flag PyInstaller-built applications. This does **not automatically mean the application is malicious**.

PyInstaller applications bundle a Python runtime and can trigger heuristic detections, particularly when an executable is relatively new or has limited distribution.

### Recommended Verification

1. Download EDMRN only from the official GitHub Releases page.
2. Check the release hash when provided.
3. Scan the executable with VirusTotal.
4. Run from source if you prefer maximum transparency.

VirusTotal: https://www.virustotal.com/

Never download EDMRN executables from unofficial mirrors.

## Overlay Compatibility

For best compatibility:

- Use **Borderless Window** mode in Elite Dangerous.
- Place the overlay away from critical HUD elements.
- Disable VSync if additional overlay responsiveness is required.

## Journal Issues

EDMRN supports automatic journal discovery and manual journal path configuration.

Default journal location:

```text
%USERPROFILE%\Saved Games\Frontier Developments\Elite Dangerous\
```

Journal logging should be enabled.

## Getting Help

- [GitHub Issues](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/issues)
- [Discord](https://discord.gg/DWvCEXH7ae)
- [Support and Community](Support-and-Community)
