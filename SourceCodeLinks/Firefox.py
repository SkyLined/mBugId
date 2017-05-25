from cSourceCodeLink import cSourceCodeLink;

# Available options:
# http://searchfox.org/mozilla-central/source/<path>#<linenumber>
# https://dxr.mozilla.org/mozilla-central/source/<path>#<linenumber>
# On windows, all paths in the symbol files are lowercased. Unfortunately, both of these options do not accept paths
# with incorrect casing, but will give a 404. The only reasonable solution I've found is to search for the file using
# dxr.mozilla.org: this allows you to automatically redirect to the correct file. Unfortunately, I have not found a
# way to pass it a line number as well.

aoSourceCodeLinks = [
  cSourceCodeLink( # base
    srPathHeader = r"c:\\builds\\moz2_slave\\m-rel-w32-00000000000000000000\\build\\src\\",
    sURLTemplate = "https://dxr.mozilla.org/mozilla-central/search?q=path:%(path)s&redirect=true",
  ),
];