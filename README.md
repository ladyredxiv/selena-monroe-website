# Selena Monroe Site

This is a plain static website for cPanel/Stellar hosting.

## Update The Site

Edit the HTML files directly, then commit and push the changes to the Git repository connected in cPanel.

Common pages:

- `index.html` - homepage
- `links.html` - link-in-bio page
- `monstrous-beloved.html` - series page
- `reading-order.html` - reading order
- `content-notes.html` - content notes
- `press.html` - press kit
- `privacy.html` - privacy policy

## Add Or Update Images

Put image files in `images/`. If a page references an image at the site root, either update the HTML to point into `images/` or add a matching root-level copy.

The current site includes root-level compatibility copies for image filenames already referenced by the HTML.

## Deploy With cPanel Git Version Control

The `.cpanel.yml` file copies the site files into `/home/seleaddv/public_html/` when cPanel deploys the repo.

If the live site files belong somewhere other than `/home/seleaddv/public_html/`, update the `DEPLOYPATH` line in `.cpanel.yml`.
