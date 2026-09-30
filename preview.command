#!/bin/bash
# Double-click to preview the site on this Mac, INCLUDING scheduled and draft posts.
# Nothing is published. Close this window (or press Control-C) to stop.
cd "$(dirname "$0")" || exit 1

fail() {
  echo
  echo "PREVIEW DID NOT START: $1"
  echo "(You can copy the messages above and send them to Claude.)"
  read -r -p "Press Return to close this window." _
  exit 1
}

echo "Checking Python..."
PY=""
for p in /usr/local/bin/python3 /opt/homebrew/bin/python3 /Library/Frameworks/Python.framework/Versions/Current/bin/python3 /usr/bin/python3; do
  if [ -x "$p" ] && "$p" -c "import sys; assert sys.version_info >= (3, 8)" 2>/dev/null; then PY="$p"; break; fi
done
if [ -z "$PY" ]; then
  xcode-select --install >/dev/null 2>&1
  fail "Python 3 isn't installed yet. A box should now appear offering to install Apple's 'command line developer tools': click Install, wait for it to finish, then double-click preview.command again. (Or install Python from https://www.python.org/downloads/ instead.)"
fi

if [ ! -x .venv/bin/python ]; then
  echo "First-time setup (takes a minute)..."
  "$PY" -m venv .venv || fail "couldn't create the preview environment."
  .venv/bin/python -m pip install --quiet --upgrade pip
  .venv/bin/python -m pip install --quiet -r requirements.txt || fail "couldn't install the helper packages (is the internet connected?)."
fi

echo "Building the preview..."
.venv/bin/python build.py --preview &
server=$!

# wait until the preview is actually running, then open it in the browser
for i in $(seq 1 90); do
  if curl -s -o /dev/null http://localhost:8000/; then
    open "http://localhost:8000/"
    echo
    echo "Preview is open in your browser. Close this window when you're done."
    wait $server
    exit 0
  fi
  kill -0 $server 2>/dev/null || fail "the build stopped with an error (see above)."
  sleep 1
done
fail "the preview took too long to start."
