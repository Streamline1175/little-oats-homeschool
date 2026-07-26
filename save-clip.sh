#!/bin/bash
# Usage: ./save-clip.sh <destination-path>
# Saves the image currently on the macOS clipboard to the given path as PNG.
DEST="$1"
osascript <<OSA
set outFile to POSIX file "$DEST"
try
  set pngData to (the clipboard as «class PNGf»)
on error
  return "ERR: no image on clipboard"
end try
set fh to open for access outFile with write permission
set eof fh to 0
write pngData to fh
close access fh
return "OK"
OSA
