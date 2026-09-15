#!/bin/zsh
# Double-click to open the local evidence explorer. No inference is started.
cd -- "${0:A:h}" || exit 1
if /usr/bin/curl --silent --fail --max-time 2 http://127.0.0.1:8765/api/bootstrap > /dev/null; then
  /usr/bin/open http://127.0.0.1:8765
else
  (
    for attempt in {1..90}; do
      sleep 1
      if /usr/bin/curl --silent --fail --max-time 2 http://127.0.0.1:8765/api/bootstrap > /dev/null; then
        /usr/bin/open http://127.0.0.1:8765
        exit 0
      fi
    done
    print 'Explorer did not become ready. Check the server message in this window.'
  ) &
  python3 -m behaviorlab explore --workspace workspace --port 8765
fi
