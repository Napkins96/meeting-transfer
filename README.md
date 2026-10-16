# Meeting Transcriber

A meeting transcriber that runs in the browser. It types what is said as people talk, or transcribes a video or audio file you give it. It starts a new paragraph when someone pauses, starts a new speaker label when the voice changes, and pulls out the key takeaways at the end.

**Use it:** https://napkins96.github.io/meeting-transfer/ (open in Google Chrome, then press **Start recording** for a live meeting, or **Transcribe a video** for a file)

## What it does

- **Live transcript.** Words appear as they are spoken, in English, Spanish or French.
- **Videos and audio files.** Press **Transcribe a video** or drag a file onto the page (MP4, MOV, WebM, M4A, MP3, WAV). The transcript fills in as it goes. When it's done, click any timestamp to play the video from that line, and the line being spoken is highlighted as it plays.
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
| 2. Speech to text | A speech model (Whisper, or the company's own) | Live: the browser's built-in speech recognizer (Web Speech API). Files: OpenAI's open-source Whisper model running in the browser through Transformers.js, on the graphics chip (WebGPU) when available |
| 3. Speaker diarization | A voiceprint for each segment, then clustering | A voiceprint per segment: 12 MFCCs (the shape of the voice's spectrum) plus the median pitch. Live, each segment joins the closest known speaker or starts a new one. On stop, every segment is regrouped by agglomerative clustering |
| 4. Summary | A language model | Rule-based on the page (line scoring, plus wording patterns for commitments, decisions and questions); Claude for a written summary |

Everything is in `index.html`: one file with no build step. The only outside code is Transformers.js, loaded from a CDN when you first transcribe a file.

### How a video gets transcribed

1. The browser decodes the file's audio track and resamples it to 16 kHz mono, the format Whisper expects.
2. Every 64 ms the page measures loudness and builds a voiceprint, which marks where the speech is and who is talking.
3. Stretches of speech are packed into windows of 28 seconds or less, cut at pauses so words aren't chopped in half. Silent stretches are skipped, which saves time and stops Whisper from inventing words over silence.
4. Whisper transcribes each window with timestamps. Each sentence gets the voiceprint of the audio under it. If one sentence holds two voices, it's split at the moment the voice changes.
5. When the file is finished, speakers are regrouped with the whole recording in view, and the takeaways are written.

## Privacy

**Video and audio files never leave your computer.** Whisper runs inside the browser; only the model itself is downloaded, once, from Hugging Face. Speaker detection, the summary and saving also run in the browser.

**Live recording is different.** In Chrome, live speech-to-text sends the audio to Google's speech service to get the words back; that is how Chrome's built-in recognizer works. Safari on recent Macs may recognize speech on the device.

## Tips

- Use Chrome on a laptop. Safari also works on recent versions of macOS. Firefox has no built-in speech recognition.
- If one person gets split into two speakers, lower **Voice-change sensitivity** or set **People in the meeting**, then press **Re-check speakers**.
- Chrome adds very little punctuation to live transcripts, so the page ends each line with a period. Whisper punctuates file transcripts itself.
- How fast a file transcribes depends on your computer. It's fastest in Chrome on a Mac with a recent chip, where the model runs on the graphics chip. The progress bar shows the time left. Files up to about 1.9 GB open in the browser. For anything bigger, export just the audio as M4A or MP3.

## Testing

`test/` holds the end-to-end tests. `make_audio.py` synthesizes a recording with two different voices, pauses, and one switch of voice mid-sentence. `run_test.py` plays it into the page as the microphone in headless Chromium, with a stand-in recognizer supplying the words. `run_video_test.py` drops it into the page as a video file, with a stand-in for Whisper supplying the words. Both print which speaker each line went to.

```bash
pip install numpy scipy playwright
python test/make_audio.py test/two_voices.wav
python test/run_test.py "$PWD/index.html" test/two_voices.wav test/screenshot.png
ffmpeg -f lavfi -i color=c=black:s=320x180:r=10 -i test/two_voices.wav -shortest -c:v libvpx -c:a libopus test/two_voices.webm
python test/run_video_test.py "$PWD/index.html" test/two_voices.webm test/video.png
```
