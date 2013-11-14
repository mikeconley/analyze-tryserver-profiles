import json
import os
import re
import sys
import tryserver

kResultRE = re.compile('TART_RESULTS_JSON=(.*?)\n')

rev = sys.argv[1]
target = sys.argv[2]
someId = sys.argv[3]

print "Getting logs for revision..."
push = tryserver.TryserverPush(rev, branch="ux", pgo=False)

logs = push.get_talos_testlogs("mountainlion", "tart")

allRuns = []

for i, log in enumerate(logs):
  allRuns = allRuns + [json.loads(s) for s in kResultRE.findall(log)]

out = os.path.join(target, someId + "-" + rev)

print "Writing to %s..." % out
with open(out, 'w') as f:
  f.write(json.dumps(allRuns))

print "Done."
