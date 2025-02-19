#define WIN32_LEAN_AND_MEAN
// disable warnings about inline functions not being inlined.
#pragma warning( disable : 4710 )
// disable warnings about bytes added as padding to align structures and class instances.
#pragma warning( disable : 4820 )
// disable warnings about Spectre mitigations
#pragma warning( disable : 5045 )

#include <roerrorapi.h>
#include <wchar.h>
#include <unknwn.h>
#include <windows.h>
#include <winstring.h>

#include "mISAArgumentParsers.h"

// For use with WRT Language errors
class cIUnknown : IUnknown {
  private:
    ULONG uRefCounter = 0;
  
  public:
    virtual ~cIUnknown() {};
    
    HRESULT STDMETHODCALLTYPE QueryInterface(REFIID pIID, PVOID* ppObject) {
      if (ppObject == NULL) {
        return E_INVALIDARG;
      } else if (!IsEqualIID(pIID, IID_IUnknown)) {
        *ppObject = NULL;
        return E_NOINTERFACE;
      } else {
        *ppObject = (PVOID)this; 
        AddRef(); 
        return NO_ERROR;
      };
    };
    
    ULONG STDMETHODCALLTYPE AddRef() {
      return ++uRefCounter;
    };
    
    ULONG STDMETHODCALLTYPE Release() {
      ULONG uReturnValue = --uRefCounter;
      if (uRefCounter == 0) {
        delete this;
      };
      return uReturnValue;
    };
};

VOID fThrowFailFastWithErrorContextForWRTError(
  const WCHAR* sHRESULTArgument,
  const WCHAR* sErrorMessageArgument,
  BOOL bLanguageError
) {
  HSTRING hString;
  HSTRING_HEADER hStringHeader;
  HRESULT hResult = CoInitialize(NULL);
  if (!SUCCEEDED(hResult)) {
    fwprintf(stderr, L"✘ CoInitialize(NULL) failed.\r\n");
    ExitProcess(1);
  };
  UINT32 uErrorMessageLength = (UINT32)wcslen(sErrorMessageArgument);
  hResult = WindowsCreateStringReference(sErrorMessageArgument, uErrorMessageLength, &hStringHeader, &hString);
  if (!SUCCEEDED(hResult)) {
    fwprintf(stderr, L"✘ WindowsCreateStringReference(0x%p, 0x%I32X, 0x%p, 0x%p) failed.\r\n",
        sErrorMessageArgument, uErrorMessageLength, &hStringHeader, &hString);
    ExitProcess(1);
  };
  wprintf(L"• Create a string reference 0x%p for error message string at 0x%p.\r\n", hString, sErrorMessageArgument);
  hResult = fhGetHRESULTForArgument(
    L"<HRESULT>", // sArgumentName
    L"a valid positive integer HRESULT value", // sArgumentType
    sHRESULTArgument // sArgument
  );
  if (SUCCEEDED(hResult)) {
    fwprintf(stderr, L"✘ <HRESULT> must be an error code, not 0x%lX because that is a success code.\r\n", hResult);
    ExitProcess(1);
  };
  if (bLanguageError) {
    IUnknown* pIUnknown = (IUnknown*)new cIUnknown();
    if (!RoOriginateLanguageException(hResult, hString, pIUnknown)) {
      fwprintf(stderr, L"✘ RoOriginateLanguageException(0x%lX, 0x%p, 0x%p) failed.\r\n", hResult, hString, pIUnknown);
      ExitProcess(1);
    };
    wprintf(L"• Reported WRT Originate language error.\r\n");
  } else {
    if (!RoOriginateError(hResult, hString)) {
      fwprintf(stderr, L"✘ RoOriginateError(0x%lX, 0x%p) failed.\r\n", hResult, hString);
      ExitProcess(1);
    };
    wprintf(L"• Reported WRT Originate error.\r\n");
  };
  if (!SUCCEEDED(RoCaptureErrorContext(hResult))) {
    fwprintf(stderr, L"✘ RoCaptureErrorContext(0x%lX) failed.\r\n", hResult);
    ExitProcess(1);
  };
  wprintf(L"• Captured previously reported error context.\r\n");
  wprintf(L"• Throwing FailFast exception with previously reported error as context...\r\n");
  RoFailFastWithErrorContext(hResult);
};
