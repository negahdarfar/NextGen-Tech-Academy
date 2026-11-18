# Offline English-to-Persian subtitle translation

An optional adapter uses Argos Translate to translate an existing English SRT
file while preserving cue numbers and timestamps. It does not transcribe audio
or automatically align subtitles to speech.

## Install

```bash
pip install argostranslate
```

Then install the English-to-Persian (`en -> fa`) language model in Argos
Translate. Availability depends on the current Argos package index; the adapter
checks installed language pairs and reports a clear error if the pair is absent.
Do not assume a translation model is installed merely because the Python
package is installed.

## Run

```bash
PYTHONPATH=src python -m nextgen_tech_academy.translate_srt captions-en.srt \
  --output build/subtitles-fa.srt
```

The tool preserves original cue timing, translates cue text locally, and
validates the resulting SRT. Human review is essential for technical terms,
names, measurements, idioms, and translation accuracy. Audio transcription
and subtitle/audio synchronization are separate steps not yet automated.
