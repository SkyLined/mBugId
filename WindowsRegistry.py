import _winreg;

gduHive_by_sName = {
  "HKCR": _winreg.HKEY_CLASSES_ROOT,
  "HKEY_CLASSES_ROOT": _winreg.HKEY_CLASSES_ROOT,
  "HKCU": _winreg.HKEY_CURRENT_USER,
  "HKEY_CURRENT_USER": _winreg.HKEY_CURRENT_USER,
  "HKLM": _winreg.HKEY_LOCAL_MACHINE,
  "HKEY_LOCAL_MACHINE": _winreg.HKEY_LOCAL_MACHINE,
  "HKU": _winreg.HKEY_USERS,
  "HKEY_USERS": _winreg.HKEY_USERS,
  "HKCC": _winreg.HKEY_CURRENT_CONFIG,
  "HKEY_CURRENT_CONFIG": _winreg.HKEY_CURRENT_CONFIG,
};
gduType_by_sName = {
  "REG_BINARY":                     _winreg.REG_BINARY,
  "REG_DWORD":                      _winreg.REG_DWORD,
  "REG_DWORD_LITTLE_ENDIAN":        _winreg.REG_DWORD_LITTLE_ENDIAN,
  "REG_DWORD_BIG_ENDIAN":           _winreg.REG_DWORD_BIG_ENDIAN,
  "REG_EXPAND_SZ":                  _winreg.REG_EXPAND_SZ,
  "REG_LINK":                       _winreg.REG_LINK,
  "REG_MULTI_SZ":                   _winreg.REG_MULTI_SZ,
  "REG_NONE":                       _winreg.REG_NONE,
  "REG_RESOURCE_LIST":              _winreg.REG_RESOURCE_LIST,
  "REG_FULL_RESOURCE_DESCRIPTOR":   _winreg.REG_FULL_RESOURCE_DESCRIPTOR,
  "REG_RESOURCE_REQUIREMENTS_LIST": _winreg.REG_RESOURCE_REQUIREMENTS_LIST,
  "REG_SZ":                         _winreg.REG_SZ,
};
gdsName_by_uType = dict([(u, s) for (s, u) in gduType_by_sName.items()]);

class cNamedValue(object):
  def __init__(oNamedValue, sName, xValue, uType = None, sType = None):
    if uType is None:
      assert sType is not None, \
          "uType or sType must be specified";
      assert sType in gduType_by_sName, \
          "Unknown sType: %s" % repr(sType);
      uType = gduType_by_sName[sType];
    elif sType is None:
      assert uType in gdsName_by_uType, \
          "Unknown uType: %s" % repr(uType);
      sType = gdsName_by_uType[uType];
    else:
      assert sType == gdsName_by_uType[uType], \
          "uType and sType mismatch: %s/%s" % (rpr(uType), repr(sType));
    oNamedValue.sName = sName;
    oNamedValue.xValue = xValue;
    oNamedValue.uType = uType;
    oNamedValue.sType = sType;

def fxGetValue(sHiveName, sKeyName, sValueName = None):
  uHive = gduHive_by_sName.get(sHiveName);
  assert uHive is not None, \
      "Unknown hive %s" % repr(sHiveName);
  oHive = _winreg.ConnectRegistry(None, uHive);
  try:
    oKey = _winreg.OpenKey(oHive, sKeyName);
    xValue, uType = _winreg.QueryValueEx(oKey, sValueName);
  except WindowsError, oWindowsError:
    if oWindowsError.errno == 2:
      return None;
    raise;
  return cNamedValue(sValueName, xValue, uType = uType);
