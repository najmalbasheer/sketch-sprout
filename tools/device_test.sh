#!/usr/bin/env bash
# Runs inside the Android emulator job: installs the APK, starts the app in test mode
# and saves a screenshot whenever the page logs "SSHOT:<name>".
set -u
APK="$1"; OUT="$2"
mkdir -p "$OUT"
adb install -r "$APK"
adb shell settings put system screen_off_timeout 1800000
adb logcat -c
adb shell am start -n com.sketchsprout.app/.MainActivity --ez autotest true
adb logcat -v raw -s SKTEST:I > "$OUT/console.log" &
LOGPID=$!
seen=0
end=$((SECONDS+7200))
while [ $SECONDS -lt $end ]; do
  total=$(wc -l < "$OUT/console.log")
  if [ "$total" -gt "$seen" ]; then
    while IFS= read -r line; do
      case "$line" in
        *SSHOT:END*) echo "test finished"; kill $LOGPID; exit 0;;
        *SSHOT:*) n=$(printf '%s' "$line" | sed -n 's/.*SSHOT:\([A-Za-z0-9_-]*\).*/\1/p'); adb exec-out screencap -p > "$OUT/$n.png"; echo "shot $n";;
      esac
    done < <(sed -n "$((seen+1)),${total}p" "$OUT/console.log")
    seen=$total
  fi
  sleep 0.2
done
echo "timed out"; kill $LOGPID; exit 1
