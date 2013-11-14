import json
import re
import urllib2
import StringIO
import cStringIO
import gzip
import zipfile
from logging import LogTrace, LogError, LogMessage, SetTracingEnabled

class TryserverPush:
  buildernames = {
    "snowleopard": {
      "tart": "Rev4 MacOSX Snow Leopard 10.6 %s%s talos svgr",
      "tpaint": "Rev4 MacOSX Snow Leopard 10.6 %s%s talos other",
      "ts_paint": "Rev4 MacOSX Snow Leopard 10.6 %s%s talos other",
      "tart": "Rev4 MacOSX Snow Leopard 10.6 %s%s talos svgr",
      "build": "OS X 10.7 %s %s build"
    },
    "lion": {
      "tart": "Rev4 MacOSX Lion 10.7 %s%s talos svgr",
      "tpaint": "Rev4 MacOSX Lion 10.7 %s%s talos other",
      "ts_paint": "Rev4 MacOSX Lion 10.7 %s%s talos other",
      "tart": "Rev4 MacOSX Lion 10.7 %s%s talos svgr",
      "build": "OS X 10.7 %s %s build"
    },
    "mountainlion": {
      "tart": "Rev5 MacOSX Mountain Lion 10.8 %s%s talos svgr",
      "tpaint": "Rev5 MacOSX Mountain Lion 10.8 %s%s talos other",
      "ts_paint": "Rev5 MacOSX Mountain Lion 10.8 %s%s talos other",
      "tart": "Rev5 MacOSX Mountain Lion 10.8 %s%s talos svgr",
      "build": "OS X 10.7 %s%s build"
    },
    "win7": {
      "tpaint": 'Windows 7 32-bit %s%s talos other',
      "ts_paint": 'Windows 7 32-bit %s%s talos other',
      "tart": 'Windows 7 32-bit %s%s talos svgr',
      "build": "WINNT 5.2 %s%s build"
    },
    "winxp": {
      "tpaint": 'Windows XP 32-bit %s%s talos other',
      "ts_paint": 'Windows XP 32-bit %s%s talos other',
      "tart": 'Windows XP 32-bit %s%s talos svgr',
      "build": "WINNT 5.2 %s%s build"
    },
    "win8": {
      "tart": 'WINNT 6.2 %s%s talos svgr',
      "build": "WINNT 5.2 %s%s build"
    },

  }

  def __init__(self, rev, branch="try", pgo=False):
    self.rev = rev
    self.branch = branch
    self.pgo = " pgo" if pgo else ""
    url = "https://tbpl.mozilla.org/php/getRevisionBuilds.php?branch=%s&rev=%s&showall=1" % (self.branch, self.rev)
    self.tbpl_runs = self._get_json(url)

  def get_talos_testlogs(self, platform, test):
    if not platform in self.buildernames:
      LogError("Unknown try platform {platform}.".format(platform=platform))
      raise StopIteration
    if not test in self.buildernames[platform]:
      LogError("Unknown test {test} on try platform {platform}.".format(platform=platform, test=test))
      raise StopIteration
    candidate = self.buildernames[platform][test] % (self.branch, self.pgo)
    print candidate
    for run in self.tbpl_runs:
      if run['buildername'] != (self.buildernames[platform][test] % (self.branch, self.pgo)):
        continue
      url = run["log"]
      LogMessage("Downloading log for talos run {logfilename}...".format(logfilename=url[url.rfind("/")+1:]))
      log = self._get_gzipped_log(url)
      testlog = self._get_test_in_log(log, test)
      yield testlog

  def get_build_symbols(self, platform):
    if not platform in self.buildernames:
      LogError("Unknown try platform {platform}.".format(platform=platform))
      return None
    dir = self._get_build_dir(platform)
    if not dir:
      return None
    symbols_zip_url = self._url_in_dir_ending_in("crashreporter-symbols.zip", dir)
    print "Final url: %s" % symbols_zip_url
    io = urllib2.urlopen(symbols_zip_url, None, 30)
    sio = cStringIO.StringIO(io.read())
    zf = zipfile.ZipFile(sio)
    io.close()
    return zf

  def _get_json(self, url):
    io = urllib2.urlopen(url, None, 30)
    return json.load(io)

  def _get_test_in_log(self, log, testname):
    match = re.compile("Running test " + testname + ":(.*?)(Running test |$)", re.DOTALL).search(log)
    return (match and match.groups()[0]) or ""

  def _get_build_dir(self, platform):
    if not platform in self.buildernames:
      LogError("Unknown try platform {platform}.".format(platform=platform))
      return ""
    buildername = self.buildernames[platform]['build'] % (self.branch, self.pgo)
    print "\nFinding buildername %s\n" % buildername
    buildruns = [run for run in self.tbpl_runs if run['buildername'] == buildername]
    if len(buildruns) < 1:
      LogError("The try push with revision {rev} does not have a build for platform {platform}.".format(rev=self.rev, platform=platform))
      return ""
    build_log_url = buildruns[0]["log"]
    return build_log_url[0:build_log_url.rfind('/')+1]

  def _get_gzipped_log(self, url):
    try:
      io = urllib2.urlopen(url, None, 30)
    except:
      return ""
    sio = StringIO.StringIO(io.read())
    io.close()
    gz = gzip.GzipFile(fileobj=sio)
    result = gz.read()
    gz.close()
    return result

  def _url_in_dir_ending_in(self, postfix, dir):
    print "Symbols URL is %s" % dir
    io = urllib2.urlopen(dir, None, 30)
    html = io.read()
    io.close()
    filename = re.search('"([^"]*' + postfix + ')"', html).groups()[0]
    return dir + filename
