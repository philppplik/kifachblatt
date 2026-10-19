# Daily PDF archive

The existing build run saves the first valid PDF for each Europe/Berlin date to report-archive/YYYY-MM-DD.pdf. Further builds may refresh the current PDF but never overwrite the dated archive. Existing dated output PDFs are imported without inventing earlier reports. Stored snapshots are restored into /berichte/ on every clean build and linked on its existing reports page.

No new dependency, hosted service, runner, workflow or polling job. Existing standard ubuntu-latest workflows remain. All three repositories were public when checked on 2026-10-19. GitHub standard hosted runners are free for public repositories: https://docs.github.com/en/actions/concepts/billing-and-usage . Scheduled Actions are best effort, not a guaranteed exact 24-hour service; delayed/missed jobs cannot reconstruct a report for a missed day.

No retention deletion. One immutable dated binary per day. Current observed PDF sizes: FA about 554 KiB (about 198 MiB/year), IW 249 KiB (about 89 MiB/year), KFB 158 KiB (about 56 MiB/year), before Git compression and other files. Actual size varies with contents. Files over 5 MiB, corrupt/truncated/non-PDF files are not archived. This caps an accidental single-file expansion, not lifetime repository growth. Git history keeps earlier binary versions; removing current files later does not shrink history. Review repository growth yearly before it approaches hosting/storage limits.

PDF rendering uses a fresh temporary file and validates PDF header, EOF, minimum size and 5 MiB cap before replacing a valid output. If rendering fails, the last stored valid report is restored. The date shown in that PDF is authoritative. A failed full build is not deployed by the existing workflow. Archive persistence uses the existing git step; a failed push is not durable archive success. No new persistence success claim is inferred from local rendering.

Tests: python3 -m unittest discover -s tools -p test_daily_archive.py . They cover Berlin date boundaries, immutable same-day snapshot, restore after clean build, render failure fallback, no automatic deletion, and seeding existing dated PDFs.
