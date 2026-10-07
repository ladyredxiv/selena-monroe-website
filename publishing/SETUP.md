# Scheduled Archive Publishing

Posts are written and reviewed in chat. The publisher runs only approved posts whose publication time has arrived. No future post HTML or metadata is copied into public_html.

## Install Once

1. The account reports Python 3.6.8, which this publisher supports without extra packages. The command uses `/usr/bin/env python3` to find the account's installed interpreter.
2. Push and deploy the repository. Deployment copies `publishing/` to `/home/seleaddv/selena-publisher/`, outside public_html, then runs the publisher. A deployment error must be fixed before enabling the scheduled task.
3. In Terminal, test `/usr/bin/env python3 /home/seleaddv/selena-publisher/publish.py --dry-run`. This reports what would publish without changing the site.
4. In cPanel Cron Jobs, choose Once Per Hour (minute 0, all other fields `*`). Use this command:

```sh
/usr/bin/env python3 /home/seleaddv/selena-publisher/publish.py
```

Set Cron Email to an address you monitor. The publisher is silent when nothing changes; publication and errors produce output for the cron notification. Do not suppress errors during setup. Schedule checks run on server time; article eligibility uses explicit timezone offsets, so server timezone does not change publication dates.

5. Confirm one real run in cPanel: the private `/home/seleaddv/selena-publisher-state/published.json` file should exist, and the archive, feed and homepage should still load. This confirms execution; adding a cron entry alone does not.

## Add A Post

Each queue entry needs the fields used by posts.json, plus:

- `approved`: explicit boolean, false until the author approves the final text and date.
- `publish_at`: ISO timestamp with offset, e.g. `2026-10-28T09:00:00-04:00` or `2026-11-18T09:00:00-05:00`. Use the Eastern offset appropriate to that date.
- `body_html`: reviewed article body; links to other site pages use `../../`.
- `note_html`: optional companion note and book links.

Drafts live under `publishing/drafts/` and never deploy as public pages. Approved entries go in `publishing/queue.json`; the queue itself remains private on the server. What the Registry Cannot Measure is approved and queued for October 28, 2026 at 9:00 a.m. Eastern. With hourly checks, it publishes on the first run at or after that time.

## Deployment And Recovery

Deployment refreshes the private homepage, archive and sitemap templates from the current repository pages, then reruns the publisher, restoring all scheduled articles from its persistent published record. Edit the public pages normally; there is no second layout copy to maintain manually. The private article template controls new article pages. Do not delete the state directory. Published entries remain public if removed from the queue or set unapproved; withdrawing a published post is a separate explicit operation.

Files are replaced individually using atomic renames. A failure midway may leave listings temporarily inconsistent; rerunning repairs them. The existing base articles and website files are not deleted. Cron runs use a lock to avoid concurrent publishers. A Git deployment may briefly reset archive listings before its final publisher step restores them.

For local verification, use `python publishing/test_publisher.py`. It uses temporary directories and never changes the live site.
