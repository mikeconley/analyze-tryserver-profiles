import argparse
import copy
import json
import os
import sys
from logging import LogTrace, LogError, LogMessage, SetTracingEnabled


def weight_profile(profile, factor):
  samples = profile["profileJSON"]["threads"]["0"]["samples"]
  for i, sample in enumerate(samples):
    weightbefore = sample["weight"] if "weight" in sample else 1
    sample["weight"] = factor * weightbefore


def merge_profiles(first, second):
  first_profile = profiles[0]
  other_profiles = profiles[1:]
  first_samples = first_profile["threads"][0]["samples"]
  for other_profile in other_profiles:
    other_samples = other_profile["threads"][0]["samples"]
    first_samples.extend(other_samples)
  return first_profile


def main(aPassedArgs):
  parser = argparse.ArgumentParser(description='Create a comparison profile.')

  parser.add_argument("-b", "--before", help="the before profile", required=True)
  parser.add_argument("-a", "--after", help="the after profile", required=True)
  parser.add_argument("-o", "--out", help="the comparison profile to create", required=True)

  args = parser.parse_args(aPassedArgs)

  beforeProfile = None
  afterProfile = None
  LogTrace("Opening before profile %s..." % args.before)
  with open(args.before, 'r') as f:
    beforeProfile = json.loads(f.read())

  LogTrace("Opening after profile %s..." % args.after)
  with open(args.after, 'r') as f:
    afterProfile = json.loads(f.read())

  LogTrace("Setting before profiles samples to negative times.")
  weight_profile(beforeProfile, -1)

  LogTrace("Merging profiles...")
  beforeSamples = beforeProfile["profileJSON"]["threads"]["0"]["samples"]
  afterSamples = afterProfile["profileJSON"]["threads"]["0"]["samples"]
  beforeSamples.extend(afterSamples)

  LogTrace('Profiles after samples: ' + str(len(beforeSamples)))
  for i, sample in enumerate(beforeSamples):
    sample["extraInfo"]["time"] = i

  LogTrace('Saving file %s...' % args.out)

  with open(args.out, 'w') as f:
    json.dump(beforeProfile, f)

if __name__ == "__main__":
  main(sys.argv[1:])