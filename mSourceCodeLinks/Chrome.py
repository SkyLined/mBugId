from .cSourceCodeLink import cSourceCodeLink;

srbBasePath = rb"\w+:(\\\w+)*\\(%s)\\src\\" % rb"|".join([
  rb"build\\slave\\(win-asan|syzygy_official|win_upload_clang)\\build",
  rb"win_asan_release",
  rb"tmp\w+\\w", # ASan builds...
  rb"win(64)?_(pgo|clang)",
  
]);

aoSourceCodeLinks = [
  cSourceCodeLink( # Blink
    srbPathHeader = srbBasePath + rb"third_party\\webkit\\source\\",
    sbFileOnlyURLTemplate = b"https://chromium.googlesource.com/chromium/src/+/master/third_party/WebKit/Source/%(path)s",
    sbFileAndLineNumberURLTemplate = b"https://chromium.googlesource.com/chromium/src/+/master/third_party/WebKit/Source/%(path)s#%(line_number)s",
  ),
  cSourceCodeLink( # syzygy
    srbPathHeader = srbBasePath + rb"syzygy\\",
    sbFileOnlyURLTemplate = b"https://github.com/google/syzygy/blob/master/syzygy/%(path)s",
    sbFileAndLineNumberURLTemplate = b"https://github.com/google/syzygy/blob/master/syzygy/%(path)s#L%(line_number)s",
  ),
  cSourceCodeLink( # V8
    srbPathHeader = srbBasePath + rb"v8\\",
    sbFileOnlyURLTemplate = b"https://chromium.googlesource.com/v8/v8.git/+/master/%(path)s",
    sbFileAndLineNumberURLTemplate = b"https://chromium.googlesource.com/v8/v8.git/+/master/%(path)s#%(line_number)s",
  ),
  cSourceCodeLink( # ASan/LLVM
    srbPathHeader = srbBasePath + rb"third_party\\llvm\\projects\\compiler-rt\\",
    sbFileOnlyURLTemplate = b"https://github.com/llvm-mirror/compiler-rt/tree/master/%(path)s",
    sbFileAndLineNumberURLTemplate = b"https://github.com/llvm-mirror/compiler-rt/tree/master/%(path)s#L%(line_number)s",
  ),
  # Anything else is assumed to be part of chromium. This is very likely not correct, as there are bound to be more
  # exceptions, so please report if you find any!
  # It is correct for the following folders: content, ipc, (list is not yet exhaustive).
  cSourceCodeLink(
    srbPathHeader = srbBasePath,
    sbFileOnlyURLTemplate = b"https://chromium.googlesource.com/chromium/src/+/master/%(path)s",
    sbFileAndLineNumberURLTemplate = b"https://chromium.googlesource.com/chromium/src/+/master/%(path)s#%(line_number)s",
  ),
];