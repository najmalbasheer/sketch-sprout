#!/usr/bin/env bash
# Runs inside the Android emulator job: installs the APK, starts the app in test mode
# and saves a screenshot whenever the page logs "SSHOT:<name>".
# The log is read with "logcat -d" (a fresh dump each time) because a streaming
# logcat written to a file is buffered and lines arrive late.
set -u
APK="$1"; OUT="$2"
mkdir -p "$OUT"
adb install -r "$APK"
adb shell settings put system screen_off_timeout 1800000
adb shell svc power stayon true
adb logcat -G 16M
echo "WebView: $(adb shell dumpsys webviewupdate | grep -m1 'Current WebView package')"
adb logcat -c
adb shell am start -n com.sketchsprout.app/.MainActivity --ez autotest true
seen=0; last=$SECONDS
end=$((SECONDS+6600))
finish(){ adb logcat -d -v time > "$OUT/logcat-full.txt" 2>/dev/null; exit "$1"; }
while [ $SECONDS -lt $end ]; do
  adb logcat -d -v raw -s SKTEST:I > "$OUT/console.log" 2>/dev/null
  total=$(wc -l < "$OUT/console.log")
  if [ "$total" -gt "$seen" ]; then
    while IFS= read -r line; do
      echo "LOG $line"
      case "$line" in
        *SSHOT:END*) echo "test finished"; finish 0;;
        *SSHOT:*) n=$(printf '%s' "$line" | sed -n 's/.*SSHOT:\([A-Za-z0-9_-]*\).*/\1/p'); adb exec-out screencap -p > "$OUT/$n.png"; last=$SECONDS;;
      esac
    done < <(sed -n "$((seen+1)),${total}p" "$OUT/console.log")
    seen=$total
  fi
  if [ $((SECONDS-last)) -gt 240 ]; then
    echo "STALLED: no screenshot for 4 minutes"
    adb exec-out screencap -p > "$OUT/zz_STALL.png"
    adb shell dumpsys activity top | head -20
    adb logcat -d -v time -s chromium:* cr_*:* AndroidRuntime:* | tail -40
    finish 1
  fi
  sleep 0.3
done
echo "timed out"; finish 1
