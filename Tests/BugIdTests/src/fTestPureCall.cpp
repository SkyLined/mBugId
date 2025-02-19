#define WIN32_LEAN_AND_MEAN
// disable warnings about inline functions not being inlined.
#pragma warning( disable : 4710 )

#include <wchar.h>
#include <windows.h>

// cPureCallBase is initialize before initializing cPureCall. cPureCallBase call fVirtual,
// which has not been initialized, causing a pure virtual function call error.
class cPureCallBase;
VOID fCallVirtual (cPureCallBase* pBase);
class cPureCallBase {
  public:
    virtual void fVirtual() = 0;
    cPureCallBase() {
      fCallVirtual(this);
    };
    virtual ~cPureCallBase() {};
};
VOID fCallVirtual (cPureCallBase* pBase) {
  pBase->fVirtual();
};
class cPureCall : cPureCallBase {
  public:
    void fVirtual() {};
};

VOID fTestPureCall() {
  wprintf(L"• Making a pure virtual function call...\r\n");
  cPureCall oPureCall;
};