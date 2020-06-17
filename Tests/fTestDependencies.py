def fTestDependencies():
  import sys;
  # Save the list of names of default loaded modules:
  def fasGetLoadedModulesNames():
    return set([
      sModuleName.split(".", 1)[0].lstrip("_")
      for sModuleName in sys.modules.keys()
    ]);
  asOriginalModuleNames = fasGetLoadedModulesNames();
  import json, os;

  # Augment the search path to make the test subject a package and have access to its modules folder.
  sTestsFolderPath = os.path.dirname(os.path.abspath(__file__));
  sMainFolderPath = os.path.dirname(sTestsFolderPath);
  sParentFolderPath = os.path.dirname(sMainFolderPath);
  sModulesFolderPath = os.path.join(sMainFolderPath, "modules");
  asOriginalSysPath = sys.path[:];
  sys.path = [sParentFolderPath, sModulesFolderPath] + asOriginalSysPath;
  # Load product details
  oProductDetailsFile = open(os.path.join(sMainFolderPath, "dxProductDetails.json"), "rb");
  try:
    dxProductDetails = json.load(oProductDetailsFile);
  finally:
    oProductDetailsFile.close();
  # Load list of dependencies on python internal modules:
  sInternalPythonModuleDepenciesListFilePath = os.path.join(sTestsFolderPath, "internal-python-module-dependencies.txt");
  if os.path.isfile(sInternalPythonModuleDepenciesListFilePath):
    oInternalPythonModuleDepenciesListFile = open(sInternalPythonModuleDepenciesListFilePath, "rb");
    try:
      sInternalPythonModuleDepenciesList = oInternalPythonModuleDepenciesListFile.read();
    finally:
      oInternalPythonModuleDepenciesListFile.close();
    asInternalPythonModuleDepencies = [s.rstrip("\r") for s in sInternalPythonModuleDepenciesList.split("\n") if s.rstrip("\r")];
  else:
    asInternalPythonModuleDepencies = [];
  # We loaded these ourselves, so they cannot be checked and do not need to be
  # specified in the list:
  asAlwaysLoadedPythonModules = ["os", "sys", "json"];

  # Load the module and all its dependencies:
  __import__(dxProductDetails["sProductName"], globals(), locals(), [], -1);
  # Determine which modules were loaded as dependencies.
  asAdditionalLoadedModuleNames = [
    sModuleName
    for sModuleName in fasGetLoadedModulesNames()
    if (
      sModuleName != dxProductDetails["sProductName"]
      and sModuleName not in asOriginalModuleNames
    )
  ];
  # Make sure nothing is loaded that is not expected to be loaded to detect new dependencies.
  asUnexpectedlyLoadedModules = list(set([
    sModuleName
    for sModuleName in asAdditionalLoadedModuleNames
    if sModuleName not in (
      dxProductDetails.get("asDependentOnProductNames", []) +
      dxProductDetails.get("asOptionalProductNames", []) +
      asAlwaysLoadedPythonModules +
      asInternalPythonModuleDepencies
    )
  ]));
  assert len(asUnexpectedlyLoadedModules) == 0, \
      "The following modules are NOT listed as a dependency but were loaded:\r\n%s" % \
      "\r\n".join(sorted(asUnexpectedlyLoadedModules, key = lambda s: unicode(s).lower()));
  # Make sure that all dependencies are in fact loaded to detect stale dependencies.
  asSuperflousDependencies = [
    sModuleName
    for sModuleName in dxProductDetails.get("asDependentOnProductNames", [])
    if sModuleName not in asAdditionalLoadedModuleNames
  ];
  assert len(asSuperflousDependencies) == 0, \
      "The following modules are listed as a dependency but not loaded:\r\n%s" % \
      "\r\n".join(sorted(asSuperflousDependencies, key = lambda s: unicode(s).lower()));
  # Make sure that all internal python modules dependencies are in fact loaded
  # to detect stale dependencies.
  asSuperflousInternalDependencies = [
    sModuleName
    for sModuleName in asInternalPythonModuleDepencies
    if (
      sModuleName not in asAdditionalLoadedModuleNames
      and sModuleName not in asAlwaysLoadedPythonModules
    )
  ];
  assert len(asSuperflousInternalDependencies) == 0, \
      "The following modules are listed as an internal python module dependency but not loaded:\r\n%s" % \
      "\r\n".join(sorted(asSuperflousInternalDependencies, key = lambda s: unicode(s).lower()));
