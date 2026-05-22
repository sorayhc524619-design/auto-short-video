# Ambient Sound Library

Place ambient loop audio files here. They are mixed (at AMBIENT_VOLUME) under the
Suno-generated music to add realism and reduce "Inauthentic Content" risk.

Recommended sources (royalty-free):
- https://freesound.org/  (CC0 / CC-BY)
- https://pixabay.com/sound-effects/
- https://mixkit.co/free-sound-effects/

Expected filenames (set in `config.AMBIENT_FILES`):

| Theme       | Filename         |
|-------------|------------------|
| rain        | rain.mp3         |
| fireplace   | fireplace.mp3    |
| forest      | forest.mp3       |
| wind        | wind.mp3         |
| ocean       | ocean.mp3        |
| thunder     | thunder.mp3      |
| stream      | stream.mp3       |

Each file should be a 5-30 minute loop in 44.1kHz stereo MP3 (or longer).
The pipeline `-stream_loop -1` will repeat them as needed.

If a file is missing, the pipeline simply skips ambient mixing and uses music only.
