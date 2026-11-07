# TDS Helper map library

Maps for [TDS Helper](https://github.com/gregurk/tds-helper), shared by
players. Every copy of the app reads `index.json` when it starts and downloads
any map that is new or has changed, so a map added here reaches everyone on
their next launch.

## Adding a map

1. In TDS Helper, scan or record the map, select it, and press **Publish**.
   That saves `your_map.tdsmap.json` to your Downloads and opens this
   repository's upload page.
2. Drag the file onto the page and press **Commit changes**.

That is all. The **rebuild map index** action checks the file and adds it to
`index.json` within a minute or two.

If the action goes red, open it: it says which file was rejected and why
(a missing spot, two spots on top of each other, a bad file name). A rejected
file is never listed, so nobody downloads it.

## Updating or removing a map

Upload a file with the same name to replace it, or delete it from `maps/`.
Apps update or drop their copy on their next start. A player's own maps are
never touched - theirs always win over the library.

## How the app trusts this

Each entry in `index.json` records the file's SHA-256, and the app refuses a
download that does not match it. Files are also re-checked inside the app
before use, with size limits and strict parsing, because everything here is
data from the internet.
