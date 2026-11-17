# Third-party services and assets

This project is independent. Counter-Strike 2, Steam, Valve, FACEIT, Leetify and OBS Studio names and marks belong to their respective owners. The project contains no FACEIT logos or assets. The overlay wordmark is constructed with local HTML and CSS. The repo bundles no font binaries and loads no remote fonts. The CSS names installed font families. Python and SQLite come from the user's Python installation. OBS, Steam, Chrome and Node are separately installed products.

`web/leetify-attribution.png` matches the provider's published White Small PNG byte for byte. Use it only for Leetify attribution under the provider's terms. The project license does not grant rights to that artwork. Its link goes to Leetify, and the profile link points to the original profile. [Leetify's published badge assets](https://drive.google.com/drive/folders/1FkJf6iseD3AOFtnOhyGkRp1fea_gKima)

Leetify's public API docs allow unauthenticated calls with tighter limits, document bearer authentication and require the developer guidelines. The overlay keeps profile snapshots in memory, uses SQLite for local GSI only, respects retry limits, and displays attribution when a provider profile is shown. The published guidelines restrict storing API data and changing the presentation of provider metrics. Leetify's interpretation of the in-memory polling cache and aggregates computed from raw match rows remains unconfirmed. [Public API specification](https://api-public-docs.cs-prod.leetify.com/) · [Developer guidelines](https://leetify.com/blog/leetify-api-developer-guidelines/)

The [demo screenshot](../assets/screenshots/preview.png) contains fictional overlay data, the project wordmark and system-rendered text. It has no Leetify data or logos.
