#!/usr/local/bin/python

import taloslog
import zlib
import sys

if len(sys.argv) > 1: 
  stuff = ""
  with open(sys.argv[1]) as f:
    stuff = f.read()

  if len(sys.argv) > 2:
    log_analyzer = taloslog.TalosLogAnalyzer(stuff)
    profiles = list(log_analyzer.get_reflow_profiles())
    print profiles[0]
  else:
    out = zlib.decompress(stuff)
    print out
