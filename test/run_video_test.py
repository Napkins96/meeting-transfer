"""Drop a two-voice test video into the page; a stand-in speech model returns the words with timestamps."""
import json, sys, time
from playwright.sync_api import sync_playwright

html, video, shot = sys.argv[1], sys.argv[2], sys.argv[3]
# (start, end, text) as spoken in the test video; the last line has two voices with no real pause
LINES = [(1.0, 4.5, 'Okay, the main goal today is to lock the launch date for the budgeting app.'),
         (5.3, 7.8, 'We have three things to cover, the beta feedback and the budget.'),
         (9.8, 12.8, 'The beta feedback was positive, about 80% said the dashboard was easy to use.'),
         (13.4, 15.4, 'I will have the retry fix ready by Friday.'),
         (21.5, 24.0, 'Should we hold back part of the budget in case the sync problem comes back?'),
         (25.0, 29.5, 'Good question, we agreed to keep five hundred in reserve and I will send the plan by Wednesday.')]
HOOK = """
window.__lines = %s; window.__calls = [];
window.__asrHook = async (audio, opts, offset) => {
  const dur = audio.length / 16000; window.__calls.push([+offset.toFixed(2), +dur.toFixed(2), opts.language]);
  await new Promise(r => setTimeout(r, 150));
  const chunks = window.__lines.filter(([a, b]) => b > offset && a < offset + dur)
    .map(([a, b, text]) => ({ timestamp: [Math.max(0, a - offset), Math.min(dur, b - offset)], text: ' ' + text }));
  return { text: chunks.map(c => c.text).join(''), chunks };
};
""" % json.dumps(LINES)

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 1280, 'height': 900})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
    pg.add_init_script(HOOK)
    pg.goto('file://' + html)
    pg.set_input_files('#fileIn', video)
    for _ in range(60):
        time.sleep(0.5)
        if pg.evaluate("!job.running && state.utts.length > 0"): break
    r = pg.evaluate("""() => ({
      calls: window.__calls, total: state.timeBase.toFixed(1),
      utts: state.utts.map(u => [u.spk, +u.t0.toFixed(2), +u.t1.toFixed(2), u.emb && u.emb.p && Math.round(u.emb.p), u.text.slice(0, 36)]),
      speakers: state.speakers.map(s => s.name), pauses: document.querySelectorAll('.pause').length,
      seekable: document.querySelectorAll('time.seek').length, player: !document.querySelector('#player').hidden,
      notice: document.querySelector('#notice').innerText.split('\\n')[0], summary: !document.querySelector('#summary').hidden })""")
    print(json.dumps(r, indent=1))
    pg.click('time.seek >> nth=2'); time.sleep(0.8)
    print('seek ->', pg.evaluate("document.querySelector('#vid').currentTime.toFixed(1)"), 'highlighted:', pg.evaluate("[...document.querySelectorAll('.u.now')].map(e=>e.textContent.slice(0,30))"))
    pg.evaluate("document.querySelector('#vid').pause()")
    print('ERRORS', errs)
    pg.screenshot(path=shot, full_page=True)
    b.close()
