#define WIN32_LEAN_AND_MEAN
// disable warnings about inline functions not being inlined.
#pragma warning( disable : 4710 )
// disable warnings about SafeInt uses some deprecated C++ features.
#pragma warning( disable : 5267 )

#include <limits.h>
#include <safeint.h>
#include <wchar.h>
#include <windows.h>

#include "mISA.h"
#include "mISAArgumentParsers.h"

VOID fTestSafeInt(
  const WCHAR* sOperationArgument,
  const WCHAR* sSignednessArgument,
  const WCHAR* sBitSizeArgument
) {
  BOOL bSigned;
  if (_wcsicmp(sSignednessArgument, L"signed") == 0) {
    bSigned = TRUE;
  } else if (_wcsicmp(sSignednessArgument, L"unsigned") == 0) {
    bSigned = FALSE;
  } else {
    fwprintf(stderr, L"✘ <Signedness> must be \"signed\" or \"unsigned\", not %s.\r\n", sSignednessArgument);
    ExitProcess(1);
  };
  ISAUINT uValueBitSize = fuGetISAUINTForArgument(
    L"<BitSize>",
    L"\"8\", \"16\", \"32\", or \"64\"",
    sBitSizeArgument
  );
  if (uValueBitSize != 8 && uValueBitSize != 16 && uValueBitSize != 32 && uValueBitSize != 64) {
    fwprintf(stderr, L"✘ <BitSize> must be \"8\", \"16\", \"32\", or \"64\", not %s.\r\n", sBitSizeArgument);
    ExitProcess(1);
  };
  if (_wcsicmp(sOperationArgument, L"++") == 0) {
    switch (uValueBitSize) {
      case 8: {
        if (bSigned) {
          msl::utilities::SafeInt<signed char> uValue = SCHAR_MAX;
          uValue++;
        } else {
          msl::utilities::SafeInt<unsigned char> uValue = UCHAR_MAX;
          uValue++;
        };
        break;
      };
      case 16: {
        if (bSigned) {
          msl::utilities::SafeInt<signed short> uValue = SHRT_MAX;
          uValue++;
        } else {
          msl::utilities::SafeInt<unsigned short> uValue = USHRT_MAX;
          uValue++;
        };
        break;
      };
      case 32: {
        if (bSigned) {
          msl::utilities::SafeInt<signed int> uValue = INT_MAX;
          uValue++;
        } else {
          msl::utilities::SafeInt<unsigned int> uValue = UINT_MAX;
          uValue++;
        };
        break;
      };
      case 64: {
        if (bSigned) {
          msl::utilities::SafeInt<signed __int64> uValue = _I64_MAX;
          uValue++;
        } else {
          msl::utilities::SafeInt<unsigned __int64> uValue = _UI64_MAX;
          uValue++;
        };
        break;
      };
    };
  } else if (_wcsicmp(sOperationArgument, L"--") == 0) {
    switch (uValueBitSize) {
      case 8: {
        if (bSigned) {
          msl::utilities::SafeInt<signed char> uValue = SCHAR_MIN;
          uValue--;
        } else {
          msl::utilities::SafeInt<unsigned char> uValue = 0;
          uValue--;
        };
        break;
      };
      case 16: {
        if (bSigned) {
          msl::utilities::SafeInt<signed short> uValue = SHRT_MIN;
          uValue--;
        } else {
          msl::utilities::SafeInt<unsigned short> uValue = 0;
          uValue--;
        };
        break;
      };
      case 32: {
        if (bSigned) {
          msl::utilities::SafeInt<signed int> uValue = INT_MIN;
          uValue--;
        } else {
          msl::utilities::SafeInt<unsigned int> uValue = 0;
          uValue--;
        };
        break;
      };
      case 64: {
        if (bSigned) {
          msl::utilities::SafeInt<signed __int64> uValue = _I64_MIN;
          uValue--;
        } else {
          msl::utilities::SafeInt<unsigned __int64> uValue = 0;
          uValue--;
        };
        break;
      };
    };
  } else if (_wcsicmp(sOperationArgument, L"*") == 0) {
    switch (uValueBitSize) {
      case 8: {
        if (bSigned) {
          msl::utilities::SafeInt<signed char> uValue = SCHAR_MIN;
          uValue *= 2;
        } else {
          msl::utilities::SafeInt<unsigned char> uValue = UCHAR_MAX;
          uValue *= 2;
        };
        break;
      };
      case 16: {
        if (bSigned) {
          msl::utilities::SafeInt<signed short> uValue = SHRT_MIN;
          uValue *= 2;
        } else {
          msl::utilities::SafeInt<unsigned short> uValue = USHRT_MAX;
          uValue *= 2;
        };
        break;
      };
      case 32: {
        if (bSigned) {
          msl::utilities::SafeInt<signed int> uValue = INT_MIN;
          uValue *= 2;
        } else {
          msl::utilities::SafeInt<unsigned int> uValue = UINT_MAX;
          uValue *= 2;
        };
        break;
      };
      case 64: {
        if (bSigned) {
          msl::utilities::SafeInt<signed __int64> uValue = _I64_MIN;
          uValue *= 2;
        } else {
          msl::utilities::SafeInt<unsigned __int64> uValue = _UI64_MAX;
          uValue *= 2;
        };
        break;
      };
    };
  } else if (_wcsicmp(sOperationArgument, L"truncate") == 0) {
    switch (uValueBitSize) {
      case 8: {
        // don't care about signedness;
        msl::utilities::SafeInt<unsigned char> uValue = 0;
        unsigned short uLargerValue = USHRT_MAX;
        uValue = uLargerValue;
        break;
      };
      case 16: {
        // don't care about signedness;
        msl::utilities::SafeInt<unsigned short> uValue = 0;
        unsigned int uLargerValue = UINT_MAX;
        uValue = uLargerValue;
        break;
      };
      case 32: {
        // don't care about signedness;
        msl::utilities::SafeInt<unsigned int> uValue = 0;
        unsigned __int64 uLargerValue = _UI64_MAX;
        uValue = uLargerValue;
        break;
      };
      case 64: {
        fwprintf(stderr, L"✘ Truncating a value into a 64-bit type is not supported.\r\n");
        ExitProcess(1);
      };
    };
  } else if (_wcsicmp(sOperationArgument, L"signedness") == 0) {
    switch (uValueBitSize) {
      case 8: {
        if (bSigned) {
          msl::utilities::SafeInt<signed char> uValue = 0;
          unsigned char uLargerValue = UCHAR_MAX;
          uValue = uLargerValue;
        } else {
          msl::utilities::SafeInt<unsigned char> uValue = 0;
          signed char uSmallerValue = SCHAR_MIN;
          uValue = uSmallerValue;
        };
        break;
      };
      case 16: {
        if (bSigned) {
          msl::utilities::SafeInt<signed short> uValue = 0;
          unsigned short uLargerValue = USHRT_MAX;
          uValue = uLargerValue;
        } else {
          msl::utilities::SafeInt<unsigned short> uValue = 0;
          signed short uSmallerValue = SHRT_MIN;
          uValue = uSmallerValue;
        };
        break;
      };
      case 32: {
        if (bSigned) {
          msl::utilities::SafeInt<signed int> uValue = 0;
          unsigned int uLargerValue = UINT_MAX;
          uValue = uLargerValue;
        } else {
          msl::utilities::SafeInt<unsigned int> uValue = 0;
          signed int uSmallerValue = INT_MIN;
          uValue = uSmallerValue;
        };
        break;
      };
      case 64: {
        if (bSigned) {
          msl::utilities::SafeInt<signed __int64> uValue = 0;
          unsigned __int64 uLargerValue = _UI64_MAX;
          uValue = uLargerValue;
        } else {
          msl::utilities::SafeInt<unsigned __int64> uValue = 0;
          signed __int64 uSmallerValue = _I64_MIN;
          uValue = uSmallerValue;
        };
        break;
      };
    };
  } else {
    fwprintf(stderr, L"✘ <Operation> must be \"++\", \"--\", \"truncate\", or \"signedness\", not %s.\r\n", sOperationArgument);
    ExitProcess(1);
  };
};
