#define WIN32_LEAN_AND_MEAN
// disable warnings about inline functions not being inlined.
#pragma warning( disable : 4710 )
// disable warnings about Spectre mitigations
#pragma warning( disable : 5045 )
// disable warnings about alloca potentially throwing an exception
#pragma warning( disable : 6255 )

#include <wchar.h>
#include <windows.h>

#include "mISA.h"
#include "mISAArgumentParsers.h"

VOID fStackRecursionLoop(ISAUINT);
VOID fStackRecursionLoopFiller(ISAUINT, ISAUINT);
ISAUINT guStackRecursionCounter = 0;

/* 
  When testing with one function call in the loop, the stack will look like this:
    fStackRecursionLoop       (loop #1)
    fStackRecursionLoop       (loop #2)
    fStackRecursionLoop       (loop #3)
    fStackRecursionLoop       (loop #4)
    ...
  When testing with two function calls in the loop, the stack will look like this:
    fStackRecursionLoop       (loop #1)
    fStackRecursionLoopFiller
    fStackRecursionLoop       (loop #2)
    fStackRecursionLoopFiller
    ...
  When testing with three function calls in the loop, the stack will look like this:
    fStackRecursionLoop       (loop #1)
    fStackRecursionLoopFiller
    fStackRecursionLoopFiller
    fStackRecursionLoop       (loop #2)
    fStackRecursionLoopFiller
    fStackRecursionLoopFiller
    ...
  etc...
*/

VOID fStackRecursionLoop(ISAUINT uMaxNumberOfCallsInALoop) {
  alloca(0x1000);
  if (uMaxNumberOfCallsInALoop == 1) {
    // Call ourselves if we only need one function calls in the loop
    fStackRecursionLoop(uMaxNumberOfCallsInALoop);
  } else {
    // Call a second function if we need more function calls in the loop
    fStackRecursionLoopFiller(uMaxNumberOfCallsInALoop, 1);
  };
};
VOID fStackRecursionLoopFiller(ISAUINT uMaxNumberOfCallsInALoop, ISAUINT uNumberOfCallsMadeInCurrentLoop) {
  alloca(0x1000);
  if (++uNumberOfCallsMadeInCurrentLoop < uMaxNumberOfCallsInALoop) {
    // Call ourselves until the total number of calls in this "loop" is the max
    fStackRecursionLoopFiller(uMaxNumberOfCallsInALoop, uNumberOfCallsMadeInCurrentLoop);
  } else {
    // Call
    fStackRecursionLoop(uMaxNumberOfCallsInALoop);
  };
};

VOID fTestStackRecursion(
  const WCHAR* sNumberOfCallsArgument
) {
  ISAUINT uMaxNumberOfCallsInALoop = fuGetISAUINTForArgument(
    L"<NumberOfCalls>",
    L"a UINT number of functions in each recursion loop",
    sNumberOfCallsArgument
  );
  wprintf(L"• Calling %Id functions recursively...\r\n", uMaxNumberOfCallsInALoop);
  fStackRecursionLoop(uMaxNumberOfCallsInALoop);
};