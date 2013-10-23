import argparse
import json
import os
import symbolication

gCleoSaved = True
gReflow = False

# Snappy symbolication server optinos
gSymbolicationOptions = {
  # Trace-level logging (verbose)
  "enableTracing": 0,
  # Fallback server if symbol is not found locally
  "remoteSymbolServer": "http://127.0.0.1:8000/",
  # Maximum number of symbol files to keep in memory
  "maxCacheEntries": 2000000,
  # Frequency of checking for recent symbols to cache (in hours)
  "prefetchInterval": 12,
  # Oldest file age to prefetch (in hours)
  "prefetchThreshold": 48,
  # Maximum number of library versions to pre-fetch per library
  "prefetchMaxSymbolsPerLib": 3,
  # Default symbol lookup directories
  "defaultApp": "FIREFOX",
  "defaultOs": "WINDOWS",
  # Paths to .SYM files, expressed internally as a mapping of app or platform names
  # to directories
  # Note: App & OS names from requests are converted to all-uppercase internally
  "symbolPaths": {
    # Location of Firefox library symbols
    "FIREFOX": os.path.join(os.getcwd(), "symbols_ffx"),
    # Location of Thunderbird library symbols
    "THUNDERBIRD": os.path.join(os.getcwd(), "symbols_tbrd"),
    # Location of Windows library symbols
    "WINDOWS": os.path.join(os.getcwd(), "symbols_os")
  }
}

def trim_samples(aProfile, aMarkerSuffix):
  measured_samples = []
  if gCleoSaved:
    samples = aProfile["profileJSON"]["threads"]["0"]["samples"]
  else:
    samples = aProfile["threads"][0]["samples"]
  in_measurement = False
  for sample in samples:
    if gReflow:
      if "marker" in sample:
        marker = sample["marker"]
        if aMarkerSuffix in marker and ":start" in marker:
          in_measurement = True
        if aMarkerSuffix in marker and ":done" in marker:
          in_measurement = False
        del sample["marker"]
    else:
      markers = None
      if gCleoSaved and "marker" in sample["extraInfo"]:
        markers = sample["extraInfo"]["marker"]
      elif not gCleoSaved and "marker" in sample:
        markers = sample["marker"]
      if markers:
        for marker in markers:
          if aMarkerSuffix in marker["name"] and ":start" in marker["name"]:
            in_measurement = True
          if aMarkerSuffix in marker["name"] and ":done" in marker["name"]:
            in_measurement = False
        if gCleoSaved:
          del sample["extraInfo"]["marker"]
        else:
          del sample["marker"]
    if in_measurement:
      measured_samples.append(sample)

  return measured_samples

def fixup_sample_data(aSamples):
  for i, sample in enumerate(aSamples):
    sample["time"] = i
    if "responsiveness" in sample:
      del sample["responsiveness"]
  return aSamples

def replace_samples(aProfile, aSamples):
  if gCleoSaved:
    aProfile["profileJSON"]["threads"]["0"]["samples"] = aSamples
  else:
    aProfile["threads"][0]["samples"] = aSamples
  return aProfile

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Trim profiles to just the samples we want.')

  parser.add_argument("-f", "--file", nargs="*", required=True, help="locally-saved profile(s)")
  parser.add_argument("-o", "--out", required=True, help="output filename")
  parser.add_argument("-ms", "--marker-suffix", required=True, help="marker suffix to filter measurements by")
  parser.add_argument("-c", "--no-cleopatra-saved", dest="cleopatra_saved", action="store_false", help="if this profile was not saved from Cleopatra")
  parser.add_argument("-s", "--symbolicate", dest="symbolicate", action="store_true", help="if we need to symbolicate the profile")
  parser.add_argument("-rp", "--reflow-profile", dest="reflow_profile", action="store_true", help="If this is a reflow profile")
  parser.set_defaults(cleopatra_saved=True, symbolicate=False, reflow_profile=False)

  args = parser.parse_args()
  gCleoSaved = args.cleopatra_saved
  gReflow = args.reflow_profile
  symbolicator = symbolication.ProfileSymbolicator(gSymbolicationOptions)

  # Get the contents of each profile...
  profiles = []

  for filename in args.file:
    with open(filename, 'r') as f:
      profiles.append(json.loads(f.read()))

  final_samples = []

  # Extract only the samples we care about
  for profile in profiles:
    if args.symbolicate:
      print "Symbolicating..."
      symbolicator.symbolicate_profile(profile)

    original_samples = None
    if gCleoSaved:
      original_samples = profile["profileJSON"]["threads"]["0"]["samples"]
    else:
      original_samples = profile["threads"][0]["samples"]
    print "Starting with %s samples..." % len(original_samples)
    samples = trim_samples(profile, args.marker_suffix)
    print "Extracted %s samples" % len(samples)
    print "Normalizing sample data"
    samples = fixup_sample_data(samples)
    final_samples += samples

  # Write out a single profile
  with open(args.out, 'w') as f:
    # Use the first profile we extracted as the shell
    # of the new profile, just replace the samples.
    json.dump(replace_samples(profiles[0], final_samples), f)

  print "Done"
