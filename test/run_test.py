"""Drive the transcriber in Chromium with the synthetic recording as the microphone and a stand-in recognizer."""
import json, sys, time
from playwright.sync_api import sync_playwright

html, wav, shot = sys.argv[1], sys.argv[2], sys.argv[3]
FINALS = [  # text the stand-in recognizer "hears", delivered ~0.7 s after each stretch of speech ends
    (5.2,  'okay the main goal today is to lock the launch date for the budgeting app'),
    (8.5,  'we have three things to cover the beta feedback and the budget'),
    (13.5, 'the beta feedback was positive about 80% said the dashboard was easy to use'),
    (16.1, 'I will have the retry fix ready by Friday'),
    (24.7, 'should we hold back part of the budget in case the sync problem comes back'),
    (30.2, 'good question we agreed to keep five hundred in reserve and I will send the plan by Wednesday'),
]
SHIM = """
window.__finals = %s;
class FakeSR { constructor(){ this.lang='en-US'; }
  start(){ if (this._s) return; this._s = 1;
    for (const [at, text] of window.__finals) setTimeout(() => this.onresult && this.onresult({ resultIndex: 0,
      results: [Object.assign([{ transcript: text, confidence: .9 }], { isFinal: true })] }), at * 1000); }
  stop(){ setTimeout(() => this.onend && this.onend(), 50); } abort(){} }
window.webkitSpeechRecognition = FakeSR; window.SpeechRecognition = FakeSR;
""" % json.dumps(FINALS)

with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream',
                                f'--use-file-for-fake-audio-capture={wav}', '--autoplay-policy=no-user-gesture-required'])
    pg = b.new_page(viewport={'width': 1280, 'height': 900})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
    pg.add_init_script(SHIM)
    pg.goto('file://' + html)
    pg.click('#recBtn'); time.sleep(31.0); pg.click('#recBtn'); time.sleep(2.5)
    r = pg.evaluate("""() => ({
      utts: state.utts.map(u => ({ spk: u.spk, t0: +u.t0.toFixed(2), t1: +u.t1.toFixed(2), n: u.emb && u.emb.n, p: u.emb && u.emb.p && Math.round(u.emb.p), text: u.text.slice(0, 40) })),
      speakers: state.speakers.map(s => s.name), thr: thr(),
      d: state.utts.map(a => state.utts.map(b => a.emb && b.emb ? +dist(a.emb, b.emb).toFixed(2) : null)),
      pauses: document.querySelectorAll('.pause').length, blocks: document.querySelectorAll('.block:not([hidden])').length,
      summary: !document.querySelector('#summary').hidden, sumText: document.querySelector('#summary').innerText.slice(0, 900) })""")
    print(json.dumps(r, indent=1)); print('ERRORS', errs)
    pg.screenshot(path=shot, full_page=True)
    b.close()
