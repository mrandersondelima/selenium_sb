#!/bin/bash

TMPFILE=$(mktemp)
mv $TMPFILE $TMPFILE.ts

BASEURL="https://gvc.live.inspiredvss.co.uk/live/soccer3sa/stream_5/"

curl -s $BASEURL$(curl -s $BASEURL/soccer3sa.m3u8 2>/dev/null|tail -n 1) -o $TMPFILE.ts; ffmpeg -i $TMPFILE.ts $TMPFILE.png 1>/dev/null 2>&1

rm -f $TMPFILE.ts

TXT=$(cat $TMPFILE.png | convert png:- -threshold 60% -crop 230x60+255+0 -negate pnm:-| gocr - 2>/dev/null)
EVENTID=$(cat $TMPFILE.png | convert png:- -threshold 95% -crop 100x34+597+15 -negate pnm:-|gocr -C "0123456789" - 2>/dev/null)

if [[ "$TXT" = "RESULT" ]]; then
  echo $TXT
  echo "$EVENTID"
  GOLS_T1=$(cat $TMPFILE.png | convert png:- -threshold 95% -crop 40x40+460+95 -negate pnm:- | gocr -C "0-8"  - 2>/dev/null )
  GOLS_T2=$(cat $TMPFILE.png | convert png:- -threshold 95% -crop 40x40+250+145 -negate pnm:- | gocr -C "0-8" - 2>/dev/null )
  echo $GOLS_T1" "$GOLS_T2
fi

rm -f $TMPFILE.png

