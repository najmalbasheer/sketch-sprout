# Sketch Sprout

A drawing-lesson app for Dua. An animated pencil shows each step on screen, she copies it on real paper, then taps "I drew it!". There are 35 lessons in coloured pencil.

## Getting the app

Every push to `main` builds a new APK on GitHub Actions. Download `SketchSprout.apk` from the latest release on the Releases page, open it on the Android device and allow "install unknown apps" when asked.

## How it is put together

- `source/preview.html` holds all the lessons and screens (the same page as the online preview).
- `tools/build_app_html.py` turns it into the offline page the app loads (`app/src/main/assets/index.html`): it removes the preview-only parts, bundles the fonts and adds saved progress, the My art gallery and back-button support.
- `app/` is a small Android app that shows that page full screen in a WebView and keeps the screen awake while she draws.
- `app/sketchsprout.keystore` signs every build with the same key, so a new version installs over the old one and keeps her progress.

To add a lesson, edit `source/preview.html` and push.
