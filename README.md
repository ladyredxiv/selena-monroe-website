# Selena Monroe Site

This is a plain static website for cPanel/Stellar hosting.

## Update The Site

For book and series updates, start with `books.json` and `series.json`. For layout or copy changes outside book data, edit the HTML files directly. Then commit and push the changes to the Git repository connected in cPanel.

Common pages:

- `index.html` - homepage
- `links.html` - link-in-bio page
- `monstrous-beloved.html` - series page
- `reading-order.html` - reading order
- `content-notes.html` - content notes
- `press.html` - press kit
- `privacy.html` - privacy policy

## Add Or Update Images

Put image files at the site root unless you also update the matching HTML and JSON paths. Current cover and brand images are referenced from root-level filenames such as `The_Binding_Night.png` and `Website_Banner.png`.

## Deploy With cPanel Git Version Control

The `.cpanel.yml` file copies the site files into `/home/seleaddv/public_html/` when cPanel deploys the repo.

If the live site files belong somewhere other than `/home/seleaddv/public_html/`, update the `DEPLOYPATH` line in `.cpanel.yml`.

## Update Books And Series

Edit `books.json` for book-level changes: release status, cover image, blurb, Amazon links, content notes links, and homepage grouping.

Edit `series.json` for series-level changes: series title, description, page URL, status, and planned book count.

The homepage loads these JSON files to build the main book section. For release updates, start in `books.json`, then update any static pages that need matching copy such as `reading-order.html`, `content-notes.html`, or the series page.
