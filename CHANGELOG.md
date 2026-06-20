# Changelog

All notable changes to The Travelling Geographer.

---

## 2026.06.20.1

- Remove Tailscale sidecar container and config

## 2026.06.16.2

- Remove obsolete Docker nginx folder; nginx now runs on host

## 2026.06.16.1

- Move nginx from Docker container to host reverse proxy

## 2026.05.29.1

- Make destination filters sticky across navigation within session

## 2026.05.22.1

- Add mDNS (Avahi) to nginx container for travel.local, enable ICMP ping

## 2026.05.20.2

- Fix selection mode click navigating instead of selecting

## 2026.05.20.1

- Add bulk select mode with Edit, Share, and Delete operations on Destinations grid view

## 2026.05.19.7

- Scope CSV export to current user's owned and shared destinations

## 2026.05.19.6

- Restrict Backup/Restore to admins; non-admins see Export tab with CSV only

## 2026.05.19.5

- User deletion: transfer or delete destinations dialog, share cleanup

## 2026.05.19.4

- Destinations search now includes tags

## 2026.05.19.3

- Tags UI fixes: merge dialog snapshot, sticky header with scrollable list, search icon style, alpha-asc default sort

## 2026.05.19.2

- Tags UI polish: checkbox spacing, single-line toolbar, clickable tags filter to Destinations

## 2026.05.19.1

- Enhanced Tags management: backend data source, search/filter, sort options, bulk merge, unused tag cleanup, admin-only bulk operations

## 2026.05.18.16

- Disable model dropdown for non-admins, add read-only notice on AI tab

## 2026.05.18.15

- Restrict AI key and prompt template editing to admins

## 2026.05.18.14

- Update Help page title and intro text

## 2026.05.18.13

- Fix Help page template and match Journal width

## 2026.05.18.12

- Match Help page width to Journal page

## 2026.05.18.11

- Add Help page with nav tab

## 2026.05.18.10

- Fix destination delete 500 (cascade shares), hide ConfirmDialog X button

## 2026.05.18.9

- Register Tooltip directive, journal date-destination layout, map scale bump

## 2026.05.18.8

- View toggle tooltips, date auto-advance, journal layout and sort, notification hint text, remove API key eye icon

## 2026.05.18.7

- Bump map scale control up 20px to clear attribution bar

## 2026.05.18.6

- Map scale toggle: metric/imperial in Settings General tab

## 2026.05.18.5

- Upcoming Trips card matches Recent Destinations layout, map scale control, satellite tile layer

## 2026.05.18.4

- Fix journal bulk endpoint: proper ORM loading and schema construction

## 2026.05.18.3

- Fix journal bulk endpoint media loading

## 2026.05.18.2

- Journal improvements: bulk endpoint, status filtering, hide tab for early statuses

## 2026.05.18.1

- Remove description field from links - model, schemas, UI, and DB migration

## 2026.05.17.9

- Set zoom options directly on Leaflet map object for smoother wheel zoom (0.25 snap)

## 2026.05.17.8

- Add wheelPxPerZoomLevel 120 for smoother mouse wheel zooming

## 2026.05.17.7

- Reduce mouse wheel zoom step to 0.5 for smoother zooming

## 2026.05.17.6

- Calculate minZoom independently for EW and NS axes, take the higher value

## 2026.05.17.5

- Allow more zoom out with getBoundsZoom inside=false, accepting some edge tile repetition

## 2026.05.17.4

- Fix minZoom calculation to use inside=true so view stays within bounds

## 2026.05.17.3

- Add dynamic minZoom based on container size and zoomSnap 0.5 for smoother map zooming

## 2026.05.17.2

- Constrain map panning to +-85 lat and +-210 lon to prevent duplicate world scrolling

## 2026.05.17.1

- Increase nginx upload limit to 500M for restore
- Fix user edit Save button disabled state
- Fix map popup: city before country, consistent font size

## 2026.05.16.16

- Convert General settings to ToggleSwitch components, remove separators

## 2026.05.16.15

- Remove System theme option, simplify to Dark/Light only

## 2026.05.16.14

- Fix system theme not reacting to OS dark/light change on Windows

## 2026.05.16.13

- Fix theme setting layout: label and hint above dropdown, left-aligned

## 2026.05.16.12

- Change theme selector from SelectButton to dropdown

## 2026.05.16.11

- Add Dark/Light/System theme setting with immediate switching

## 2026.05.16.10

- Change mobile stat cards to single column

## 2026.05.16.9

- Revert mobile stat cards to simple 2-column grid

## 2026.05.16.8

- Add small downward arrows on mobile timeline connector

## 2026.05.16.7

- Replace mobile chevrons with vertical timeline connector line

## 2026.05.16.6

- Add vertical downward chevron arrows on mobile Dashboard

## 2026.05.16.5

- Add clip-path chevron arrows to Dashboard stat cards

## 2026.05.16.4

- Add license text popup from About dialog

## 2026.05.16.3

- Update copyright name to John E Parks

## 2026.05.16.2

- Add MIT License
- Add copyright and license info to About dialog
- Replace view toggle with SelectButton component
- Fix thumbnail 404s with on-demand generation
- Reduce mobile padding across all views
- Fix Journal tab not loading all destinations

## 2026.05.16.1

- Fix thumbnail 404s with on-demand generation
- Reduce mobile padding on Destination Detail, Settings, Users, Journal views
- Replace view toggle buttons with SelectButton component
- Fix Journal tab not loading all destinations

## 2026.05.12.1

- Rename Docker container tg-database to tg-db and add image names to docker-compose
- Merge auth implementation into app spec, drop OAuth and MFA phases
- Add About dialog with version tracking, changelog, and bump-version script
- Move Settings and Users into user dropdown menu
- Switch token storage from sessionStorage to localStorage for cross-tab persistence

## 2026.05.09.1
- Add user authentication system with JWT tokens, setup wizard, login/register, and user management
- Add password complexity requirements (12 chars, upper/lower/number/symbol) with real-time validation
- Fix backup/restore SSE endpoints to use query-param auth (EventSource cannot send headers)
- Fix double delete confirmation dialog in user management
- Fix last_login not set on registration and setup auto-login
- Fix toast notifications ignoring the show-notifications setting
- Switch token storage from sessionStorage to localStorage for cross-tab sessions
- Move Settings and Users links into a user dropdown menu in the navbar
- Add About dialog with version tracking and changelog
