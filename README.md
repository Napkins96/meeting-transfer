# Meeting Transcriber

A meeting transcriber that runs in the browser. It types what is said as people talk, starts a new paragraph when someone pauses, starts a new speaker label when the voice changes, and pulls out the key takeaways when you stop.

**Use it:** https://napkins96.github.io/meeting-transfer/ (open in Google Chrome, press **Start recording**, allow the microphone)

## What it does

- **Live transcript.** Words appear as they are spoken, in English, Spanish or French.
- **Pauses.** A short pause starts a new paragraph (you set how short). A long pause gets a marker such as `pause · 7 s`.
- **Speaker changes.** Each stretch of speech gets a voiceprint. A voice that doesn't match anyone heard so far gets a new label, even mid-sentence. When you stop, it regroups every stretch with the whole recording in view.
- **Corrections.** Rename speakers, and click any line to move it to the right person.
- **Key takeaways.** When you stop: main points, action items with who said them, decisions, open questions, topics and each person's share of talk time.
- **Export.** Copy, or download as `.txt` or Markdown. **Summarize with Claude** copies the transcript and opens a Claude page that writes a full summary.
- **Saved as you go.** If the tab closes by accident, the transcript is offered back the next time you open the page.

## How it works

Professional tools (Otter, Rev, Descript, and open-source pipelines such as WhisperX with pyannote) follow the same four steps. This project builds each one in plain JavaScript:

| Step | What pro tools do | What this project does |
|---|---|---|
| 1. Voice activity detection | A model marks where speech starts and stops | Measures loudness ~23 times a second against a background level it learns from the room; speech must stay above it for 2 frames to start and drop below it for 0.3 s to end |
| 2. Speech to text | A speech model (Whisper, or the company's own) | The browser's built-in speech recognizer (Web Speech API) |
| 3. Speaker diarization | A voiceprint for each segment, then clustering | A voiceprint per segment: 12 MFCCs (the shape of the voice's spectrum) plus the median pitch. Live, each segment joins the closest known speaker or starts a new one. On stop, every segment is regrouped by agglomerative clustering |
| 4. Summary | A language model | Rule-based on the page (line scoring, plus wording patterns for commitments, decisions and questions); Claude for a written summary |

Everything is in `index.html`: one file with no build step and no dependencies.

## Privacy

Speaker detection, the summary and saving all run inside your browser. In Chrome, **speech-to-text sends the audio to Google's speech service** to get the words back; that is how Chrome's built-in recognizer works. Safari on recent Macs may recognize speech on the device.

## Tips

- Use Chrome on a laptop. Safari also works on recent versions of macOS. Firefox has no built-in speech recognition.
- If one person gets split into two speakers, lower **Voice-change sensitivity** or set **People in the meeting**, then press **Re-check speakers**.
- Chrome adds very little punctuation, so the page ends each line with a period.

## Testing

`test/` holds the end-to-end test. `make_audio.py` synthesizes a recording with two different voices, pauses, and one switch of voice mid-sentence. `run_test.py` plays it into the page as the microphone in headless Chromium, with a stand-in recognizer supplying the words, and prints which speaker each line went to.

```bash
pip install numpy scipy playwright
python test/make_audio.py test/two_voices.wav
python test/run_test.py "$PWD/index.html" test/two_voices.wav test/screenshot.png
```
