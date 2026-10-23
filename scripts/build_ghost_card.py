"""Build a self-contained, style-isolated Ghost HTML card from the report."""
from pathlib import Path
import html

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'docs/reviewer-milestone-20261022'
source = (DEST / 'index.html').read_text()
# External source links should open outside the embedded report. Fragment links
# stay local and ask the host to scroll, avoiding a giant nested scrolling area.
bridge = r'''
<script>
(function () {
  const signal = 'behavior-lab-ghost-v1';
  const send = (type, value) => parent.postMessage({signal, type, value}, '*');
  let lastHeight = 0;
  const size = () => {
    const height = Math.ceil(Math.max(document.body.scrollHeight, document.body.getBoundingClientRect().height));
    if (Math.abs(height - lastHeight) > 1) { lastHeight = height; send('height', height); }
  };
  new ResizeObserver(size).observe(document.body);
  addEventListener('load', size);
  document.fonts?.ready.then(size);
  document.querySelectorAll('a[href^="https:"]').forEach(a => { a.target = '_blank'; a.rel = 'noopener noreferrer'; });
  document.addEventListener('click', event => {
    const a = event.target.closest('a[href^="#"]');
    if (!a) return;
    event.preventDefault();
    const id = a.getAttribute('href').slice(1);
    const target = id ? document.getElementById(id) : document.body;
    if (target) send('scroll', Math.max(0, target.getBoundingClientRect().top + scrollY - 24));
  });
  // Clipboard permission is commonly unavailable in sandboxed frames.
  // Keep the existing download alternative and its explicit no-submission message.
  size();
})();
</script>
'''
source = source.replace('</body>', bridge + '</body>')
card = '''<!-- Behavior Laboratory: paste this entire file into ONE Ghost HTML card.
     Self-contained report/data. No Ghost theme or code-injection changes needed.
     Interactive content is for the web post; use the fallback link in email. -->
<div class="kg-width-wide" data-behavior-lab-ghost style="display:block!important;width:100%!important;max-width:100%!important;margin:24px 0!important;padding:0!important;">
  <p style="font:inherit;margin:0 0 12px;">Interactive research report · <a href="https://ebergel.github.io/ai-behavior-lab/" target="_blank" rel="noopener noreferrer">Open the report in a separate tab</a></p>
  <iframe title="Behavior Laboratory — interactive research milestone" sandbox="allow-scripts allow-downloads allow-popups allow-popups-to-escape-sandbox allow-modals" referrerpolicy="no-referrer" style="display:block!important;width:100%!important;max-width:100%!important;height:760px;border:1px solid #d4dcd2!important;border-radius:6px!important;margin:0!important;padding:0!important;background:#f5f3eb!important;" srcdoc="''' + html.escape(source, quote=True) + '''"></iframe>
  <noscript><p>JavaScript is required for the interactive plots. <a href="https://ebergel.github.io/ai-behavior-lab/">Read the report on GitHub Pages.</a></p></noscript>
</div>
<script>
(function () {
  const card = document.currentScript.previousElementSibling;
  const frame = card.querySelector('iframe');
  // Each pasted card gets its own frame and handler; no global IDs or CSS.
  window.addEventListener('message', function (event) {
    if (event.source !== frame.contentWindow) return;
    const data = event.data;
    if (!data || data.signal !== 'behavior-lab-ghost-v1' || !Number.isFinite(data.value)) return;
    if (data.type === 'height' && data.value > 0 && data.value < 100000) {
      frame.style.setProperty('height', Math.ceil(data.value) + 2 + 'px', 'important');
    } else if (data.type === 'scroll' && data.value >= 0 && data.value <= frame.offsetHeight) {
      window.scrollTo({top: frame.getBoundingClientRect().top + window.scrollY + data.value, behavior: 'smooth'});
    }
  });
})();
</script>
'''
(DEST / 'ghost-html-card.html').write_text(card)
# Plain-text extension makes downloading and copying the code straightforward.
(DEST / 'ghost-html-card.txt').write_text(card)
print(f'Wrote self-contained Ghost card: {len(card.encode()):,} bytes')
