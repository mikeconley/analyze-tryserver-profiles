import argparse
import copy
import json
import os
import sys
from logging import LogTrace, LogError, LogMessage, SetTracingEnabled


def get_interesting_times(aStart, aEnd, aMarkers):
  interestingTimes = []
  inInterestingTime = False
  currentTime = [None, None]
  for marker in aMarkers:
    if marker['name'] == aStart and not inInterestingTime:
      currentTime[0] = marker['time']
      inInterestingTime = True
    if marker['name'] == aEnd and inInterestingTime:
      currentTime[1] = marker['time']
      interestingTimes.append(copy.copy(currentTime))
      inInterestingTime = False
  return interestingTimes


def get_interesting_samples(aTimes, aSamples):
  interestingSamples = []
  inInterestingTime = False
  currentTime = aTimes.pop(0)
  for sample in aSamples:
    sampleTime = sample['extraInfo']['time']

    if inInterestingTime and (sampleTime > currentTime[1]):
      inInterestingTime = False
      if len(aTimes) == 0:
        break
      currentTime = aTimes.pop(0)

    if not inInterestingTime and (sampleTime > currentTime[0]) and (sampleTime < currentTime[1]):
      inInterestingTime = True

    if inInterestingTime:
      interestingSamples.append(sample)

  return interestingSamples


def main(aPassedArgs):
  parser = argparse.ArgumentParser(description='Boil down a saved SPS profile into just the interesting samples.')

  parser.add_argument("-f", "--file", nargs="*", help="locally-saved log file(s)", required=True)
  parser.add_argument("-o", "--out", help="output filename", required=True)
  parser.add_argument("-m", "--marker", help="marker to look for, minus the start/end suffixes", required=True)
  parser.add_argument("-s", "--start-suffix", help="start suffix for each marker", default="start")
  parser.add_argument("-e", "--end-suffix", help="end suffix for each marker", default="end")
  parser.add_argument("-rp", "--reflow-profile", help="specify to extract reflow profiles instead of SPS profiles", action="store_true")

  args = parser.parse_args(aPassedArgs)

  originalProfiles = []
  startMarker = "%s:%s" % (args.marker, args.start_suffix)
  endMarker = "%s:%s" % (args.marker, args.end_suffix)
  LogTrace("I will be extracting samples between markers %s and %s." % (startMarker, endMarker))

  for aLogFile in args.file:
    # Open the file, extract the JSON
    LogTrace("Loading profile from %s" % aLogFile)
    with open(aLogFile, 'r') as f:
  	  originalProfiles.append(json.loads(f.read()))

  LogTrace("Successfully loaded %s profiles." % (len(originalProfiles)))
  LogTrace("Creating shell for final profile.")
  finalProfile = copy.deepcopy(originalProfiles[0])
  # Clear out the samples and markers from the final profile.
  finalProfileThread = finalProfile['profileJSON']['threads']['0']
  finalProfileThread['markers'] = []
  finalProfileThread['samples'] = []

  for profile in originalProfiles:
    profileThread = profile['profileJSON']['threads']['0']
    markers = profileThread['markers']
    LogTrace("There are %s markers in this profile." % len(markers))
    samples = profileThread['samples']
    interestingTimes = get_interesting_times(startMarker, endMarker, markers)
    LogTrace("Extracted %s interesting time ranges in a profile." % len(interestingTimes))
    interestingSamples = get_interesting_samples(interestingTimes, samples)
    LogTrace("Extracted %s interesting samples from a profile." % len(interestingSamples))
    finalProfileThread['samples'] = finalProfileThread['samples'] + interestingSamples

  LogTrace("Fixing up timing data in final profile.")
  for i, sample in enumerate(finalProfileThread['samples']):
    sample["extraInfo"]["time"] = i

  LogTrace("Writing out final distilled profile to %s." % args.out)
  with open(args.out, 'w') as f:
    json.dump(finalProfile, f)

  LogTrace("We're done here.")

if __name__ == "__main__":
	main(sys.argv[1:])