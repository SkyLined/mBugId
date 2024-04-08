import datetime, re;

gasbMonths = [b"Jan", b"Feb", b"Mar", b"Apr", b"May", b"Jun", b"Jul", b"Aug", b"Sep", b"Oct", b"Nov", b"Dec"];
grbDebuggerTime = re.compile(
  rb"^\s*"
  rb"(Mon|Tue|Wed|Thu|Fri|Sat|Sun)"                         # * Weekday
  rb"\s+"                                                   #   whitespace
  rb"(" + rb"|".join(gasbMonths) + rb")"                    # * Month
  rb"\s+"                                                   #   whitespace
  rb"(\d+)"                                                 # * Day in month
  rb"\s+"                                                   #   whitespace
  rb"(\d+):(\d+):(\d+).(\d+)"                               # * Hour ":" Minute ":" Second "." Millisecond
  rb"\s+"                                                   #   whitespace
  rb"(\d+)"                                                 # * Year
  rb"\s+"                                                   #   whitespace
  rb"\(.*\)"                                                #  "(" Timezone ")"
  rb"\s*$"
);

def fnGetDebuggerTimeInSeconds(sbDebuggerTime):
  # Parse .time and .lastevent timestamps; return a number of seconds since an arbitrary but constant starting point in time.
  obDebuggerTimeMatch = grbDebuggerTime.match(sbDebuggerTime);
  assert obDebuggerTimeMatch, \
    "Cannot parse debugger time: %s" % repr(sbDebuggerTime);
  (sbWeekDay, sbMonth, sbDay, sbHour, sbMinute, sbSecond, sbMillisecond, sbYear) = \
      obDebuggerTimeMatch.groups();
  oDateTime = datetime.datetime(
    int(sbYear),
    gasbMonths.index(sbMonth) + 1,
    int(sbDay),
    int(sbHour),
    int(sbMinute),
    int(sbSecond),
    int(sbMillisecond.ljust(6, b"0")),
  );
  # Convert to a floating point number by calculating the number of seconds since
  # an arbitrarily chosen epoch.
  return (oDateTime - datetime.datetime(1976,8,28)).total_seconds();

