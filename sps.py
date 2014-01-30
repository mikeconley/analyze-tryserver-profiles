import json

def filter_measurements(profile, is_startup_test=False, marker_suffix=None, is_reflow_profile=False, key=0):
  startMeasurementMarker = "MEASUREMENT_START"
  stopMeasurementMarker = "MEASUREMENT_STOP"

  if marker_suffix:
    startMeasurementMarker = stopMeasurementMarker = marker_suffix

  if is_reflow_profile:
    samples = profile["threads"][key]["samples"]
    measured_samples = []
    in_measurement = is_startup_test
    for sample in samples:
      if "marker" in sample:
        aMarker = sample["marker"]
        if startMeasurementMarker in aMarker and "start" in aMarker:
          in_measurement = True
        if stopMeasurementMarker in aMarker and "end" in aMarker:
          in_measurement = False
        del sample["marker"]
      if in_measurement:
        measured_samples.append(sample)
    profile["threads"][key]["samples"] = measured_samples
    return profile
  else:
    samples = profile["threads"][key]["samples"]
    measured_samples = []
    in_measurement = is_startup_test
    for sample in samples:
      info = sample['extraInfo']
      if "marker" in info:
        for aMarker in info['marker']:
          if startMeasurementMarker in aMarker['name'] and "start" in aMarker['name']:
            in_measurement = True
            break
          if stopMeasurementMarker in aMarker['name'] and "done" in aMarker['name']:
            in_measurement = False
            break
        del info["marker"]
      if in_measurement:
        measured_samples.append(sample)
    profile["threads"][key]["samples"] = measured_samples
    return profile

def merge_profiles(profiles):
  first_profile = profiles[0]
  other_profiles = profiles[1:]
  first_samples = first_profile["threads"][0]["samples"]
  for other_profile in other_profiles:
    other_samples = other_profile["threads"][0]["samples"]
    first_samples.extend(other_samples)
  return first_profile

def fixup_sample_data(profile):
  samples = profile["threads"][0]["samples"]
  for i, sample in enumerate(samples):
    sample["time"] = i
    if "responsiveness" in sample:
      del sample["responsiveness"]


def compress_profile(profile):
  symbols = set()
  for thread in profile["threads"]:
    for sample in thread["samples"]:
      for frame in sample["frames"]:
        if isinstance(frame, basestring):
          symbols.add(frame)
        else:
          symbols.add(frame["location"])
  location_to_index = dict((l, str(i)) for i, l in enumerate(symbols))
  for thread in profile["threads"]:
    for sample in thread["samples"]:
      for i, frame in enumerate(sample["frames"]):
        if isinstance(frame, basestring):
          sample["frames"][i] = location_to_index[frame]
        else:
          frame["location"] = location_to_index[frame["location"]]
  profile["format"] = "profileJSONWithSymbolicationTable,1"
  profile["symbolicationTable"] = dict(enumerate(symbols))
  profile["profileJSON"] = { "threads": profile["threads"] }
  del profile["threads"]

def save_profile(profile, filename):
  f = open(filename, "w")
  json.dump(profile, f)
  f.close()
