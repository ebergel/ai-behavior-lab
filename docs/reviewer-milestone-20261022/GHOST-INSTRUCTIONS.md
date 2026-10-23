# Add the report to a Ghost post

1. Open `ghost-html-card.txt` in a plain-text editor and copy **all** its contents.
2. In a Ghost post on t333t.com, type `/html` and select **HTML**.
3. Paste into that one HTML card. Do not paste it into a Markdown or Code card.
4. Preview the **web post**. The report should expand vertically and its topic, measure, sorting and length controls should work.
5. Publish when ready. No theme edits, global code injection or file uploads are required.

The card contains the entire report and data. A sandboxed iframe isolates report styles and scripts from the Ghost theme. Its height adjusts to the content; internal section links scroll the containing post. External evidence links open in a new tab. The optional `kg-width-wide` class uses the theme's wide-card support; otherwise the report fits the normal post column.

If the Ghost editor's inline preview does not run scripts, use the post's web preview. A custom Content Security Policy that disallows inline scripts or frames may need site-specific adjustment; this has not been tested on the live t333t.com installation. If blocked, the standalone report link remains available. Copy-to-clipboard may be unavailable in the sandbox; Download .txt remains the feedback alternative.

Interactive JavaScript/frames do not work in email newsletters. Keep the standalone report link for email readers or set this card to web-only and add an email-only link card. Ghost explains this limitation at https://ghost.org/help/can-i-use-embeds-in-email-newsletters/ .

The card never submits comments automatically. No edits or publication have been made to t333t.com.

## Updating

`index.html` is the source report. Regenerate both paste-ready files with:

```sh
python3 scripts/build_ghost_card.py
```

The embedded report is a snapshot: later GitHub Pages changes do not automatically change a card already pasted into Ghost. Paste the regenerated card to update the post.
