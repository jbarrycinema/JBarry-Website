# jackabarry.com

Static portfolio for Jack Barry, cinematographer. One `index.html`, no build step, hosted on GitHub Pages.

## Layout

```
index.html        page, styles and script
palettes.js       per-second colours sampled from each video (drives the hover light)
media/            <slug>.av1.mp4, <slug>.hevc.mp4, <slug>.webp poster
tools/            encode + palette scripts, local preview server
```

Projects are listed in the `FILM` and `OPERATING` arrays near the top of the script in `index.html`. A project with a `slug` plays `media/<slug>.*`; a project with an `image` shows that still; a project with neither shows a "Footage coming soon" card.

## Video formats

Every video ships in two encodes. The page picks one at load:

| File | Codec | Who gets it |
|---|---|---|
| `<slug>.av1.mp4` | AV1 10-bit (SVT-AV1) | Chrome, Edge, Firefox, Safari on M3 / iPhone 15 Pro and newer |
| `<slug>.hevc.mp4` | HEVC 8-bit, `hvc1` | Older Safari and iPhones, plus phones with only software AV1 decoding |

Both are `+faststart` (playback starts on the first bytes), and trailers have no audio track. Together both encodes come to about a third of the original MP4s (roughly 340 MB against 935 MB), and every file stays under GitHub's 50 MB warning.

## Add or replace a video

Needs `ffmpeg` (with libsvtav1, libx265, libwebp) and Python 3 with numpy.

```bash
tools/encode.sh "$HOME/Desktop/New Trailer.mp4" new-trailer trailer
```

Use `long` instead of `trailer` for anything that should keep its sound. Then add an entry with `slug: 'new-trailer'` to `FILM` or `OPERATING` in `index.html`.

## Preview locally

```bash
python3 tools/serve.py . 8765
```

Then open http://localhost:8765. This server supports range requests like GitHub Pages does, which `python3 -m http.server` does not, so looping and seeking behave the same as on the live site.

## GitHub Pages limits

Published site under 1 GB, files under 100 MB (50 MB warning), no Git LFS (Pages serves LFS pointer files, not the video). Each re-encode adds to the repository's history, so replace videos sparingly or squash history if the repo approaches 1 GB.

## Contact form

The inquiry form on the Contact page posts to [Web3Forms](https://web3forms.com) from the browser; there's no server. The access key is the `WEB3FORMS_KEY` constant in `index.html`. It is public by design and only allows sending to the inbox it was created with. To change the receiving inbox, create a new key at web3forms.com and replace the constant.

Spam protection is a hidden `botcheck` honeypot. If spam gets through, enable hCaptcha in the Web3Forms dashboard and add their hCaptcha snippet to the form.
