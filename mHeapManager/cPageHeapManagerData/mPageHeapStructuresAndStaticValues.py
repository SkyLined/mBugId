from mWindowsSDK import \
  iStructureType32, iStructureType64, UNION, STRUCT, \
  CHAR, UCHAR, WORD, ULONG, \
  UINT32, UINT64, \
  SIZE_T32, SIZE_T64, \
  P32VOID, P64VOID;

# SINGLE_LIST_ENTRY
SINGLE_LIST_ENTRY32 = iStructureType32.fcCreateClass("SINGLE_LIST_ENTRY32",
  (P32VOID,         "Next"),                          # PSINGLE_LIST_ENTRY
);
SINGLE_LIST_ENTRY64 = iStructureType64.fcCreateClass("SINGLE_LIST_ENTRY64",
  (P64VOID,         "Next"),                          # PSINGLE_LIST_ENTRY
);
# LIST_ENTRY
LIST_ENTRY32 = iStructureType32.fcCreateClass("LIST_ENTRY32",
  (P32VOID,         "pBLink"),                        # PLIST_ENTRY32
  (P32VOID,         "pFLink"),                        # PLIST_ENTRY32
);
LIST_ENTRY64 = iStructureType64.fcCreateClass("LIST_ENTRY64",
  (P64VOID,         "pBLink"),                        # PLIST_ENTRY64
  (P64VOID,         "pFLink"),                        # PLIST_ENTRY64
);
# RTL_BALANCED_LINKS
RTL_BALANCED_LINKS32 = iStructureType32.fcCreateClass("RTL_BALANCED_LINKS32",
  (P32VOID,         "Parent"),                        # PRTL_BALANCED_LINKS
  (P32VOID,         "LeftChild"),                     # PRTL_BALANCED_LINKS
  (P32VOID,         "RightChild"),                    # PRTL_BALANCED_LINKS
  (CHAR,            "Balance"),
  (UCHAR[3],        "Reserved"),
);
RTL_BALANCED_LINKS64 = iStructureType64.fcCreateClass("RTL_BALANCED_LINKS64",
  (P64VOID,         "Parent"),                        # PRTL_BALANCED_LINKS
  (P64VOID,         "LeftChild"),                     # PRTL_BALANCED_LINKS
  (P64VOID,         "RightChild"),                    # PRTL_BALANCED_LINKS
  (CHAR,            "Balance"),
  (UCHAR[3],        "Reserved"),
);
# DPH_DELAY_FREE_FLAGS
DPH_DELAY_FREE_FLAGS32 = iStructureType32.fcCreateClass("DPH_DELAY_FREE_FLAGS32",
  (UINT32,          "All"),
);
DPH_DELAY_FREE_FLAGS64 = iStructureType64.fcCreateClass("DPH_DELAY_FREE_FLAGS64",
  (UINT32,          "All"),
);
DPH_DELAY_FREE_FLAGS_PageHeapBlock    = 1 << 0;
DPH_DELAY_FREE_FLAGS_NormalHeapBlock  = 1 << 1;
DPH_DELAY_FREE_FLAGS_Lookaside        = 1 << 2;
# DPH_DELAY_FREE_QUEUE_ENTRY
DPH_DELAY_FREE_QUEUE_ENTRY32 = iStructureType32.fcCreateClass("DPH_DELAY_FREE_QUEUE_ENTRY32",
  (DPH_DELAY_FREE_FLAGS32, "Flags"),
  (P32VOID,         "NextEntry"),                     # DPH_DELAY_FREE_QUEUE_ENTRY
);
DPH_DELAY_FREE_QUEUE_ENTRY64 = iStructureType64.fcCreateClass("DPH_DELAY_FREE_QUEUE_ENTRY64",
  (DPH_DELAY_FREE_FLAGS64, "Flags"),
  (P64VOID,         "NextEntry"),                     # DPH_DELAY_FREE_QUEUE_ENTRY
);
# DPH_HEAP_BLOCK_FLAGS
DPH_HEAP_BLOCK_FLAGS32 = iStructureType32.fcCreateClass("DPH_HEAP_BLOCK_FLAGS32",
  (UINT32,          "All"),
);
DPH_HEAP_BLOCK_FLAGS64 = iStructureType64.fcCreateClass("DPH_HEAP_BLOCK_FLAGS64",
  (UINT32,          "All"),
);
DPH_HEAP_BLOCK_FLAGS_UnusedNode       = 1 << 1;
DPH_HEAP_BLOCK_FLAGS_Delay            = 1 << 2;
DPH_HEAP_BLOCK_FLAGS_Lookaside        = 1 << 3;
DPH_HEAP_BLOCK_FLAGS_Free             = 1 << 4;
DPH_HEAP_BLOCK_FLAGS_Busy             = 1 << 5;
# DPH_HEAP_BLOCK
bUseNewPageHeapStructures = True;
if not bUseNewPageHeapStructures:
  DPH_HEAP_BLOCK32 = iStructureType32.fcCreateClass("DPH_HEAP_BLOCK32",
    UNION (
      (P32VOID,       "pNextAlloc"),                      # PDPH_HEAP_BLOCK
      (LIST_ENTRY32,  "AvailableEntry"),
      (RTL_BALANCED_LINKS32, "TableLinks"),
    ),
    (P32VOID,         "pUserAllocation"),
    (P32VOID,         "pVirtualBlock"),
    (SIZE_T32,        "nVirtualBlockSize"),
    (UINT32,          "uState"),                          # I've only seen 4 (free) and 20 (allocated)
    (UINT32,          "nUserRequestedSize"),
    (LIST_ENTRY32,    "AdjacencyEntry"),
    (P64VOID,         "pVirtualRegion"),
    (P32VOID,         "StackTrace"),                      # PRTL_TRACE_BLOCK
  );
  DPH_HEAP_BLOCK64 = iStructureType64.fcCreateClass("DPH_HEAP_BLOCK64",
    UNION (
      (P64VOID,       "pNextAlloc"),                      # PDPH_HEAP_BLOCK
      (LIST_ENTRY64,  "AvailableEntry"),
      (RTL_BALANCED_LINKS64, "TableLinks"),
    ),
    (P64VOID,         "pUserAllocation"),
    (P64VOID,         "pVirtualBlock"),
    (SIZE_T64,        "nVirtualBlockSize"),
    (UINT32,          "uState"),                          # I've only seen 4 (free) and 20 (allocated)
    (UINT64,          "nUserRequestedSize"),
    (LIST_ENTRY64,    "AdjacencyEntry"),
    (P64VOID,         "pVirtualRegion"),
    (P64VOID,         "StackTrace"),                      # PRTL_TRACE_BLOCK
  );
  DPH_STATE_ALLOCATED = 0x20;
  DPH_STATE_FREED = 0x4;
else:
  # On Windows 11 I am encountering a different format for Page heap blocks:
  # Reference: https://doxygen.reactos.org/d5/df0/struct__DPH__HEAP__BLOCK.html
  # Reference: https://mail.nirsoft.net/kernel_struct/vista/DPH_HEAP_BLOCK.html
  DPH_HEAP_BLOCK32 = iStructureType32.fcCreateClass("DPH_HEAP_BLOCK32",
    UNION (
      (P32VOID,         "pNextAlloc"),                      # PDPH_HEAP_BLOCK
      (LIST_ENTRY32,    "AvailableEntry"),
      (RTL_BALANCED_LINKS32, "TableLinks"),
    ),
    (P32VOID,           "pUserAllocation"),
    (P32VOID,           "pVirtualBlock"),
    (UINT32,            "nVirtualBlockSize"),
    (UINT32,            "nVirtualAccessSize"),
    (UINT32,            "nUserRequestedSize"),
    (UINT32,            "nUserActualSize"),
    (P32VOID,           "UserValue"),
    (UINT32,            "UserFlags"),
    (P32VOID,           "StackTrace"),    #PRTL_TRACE_BLOCK
    (LIST_ENTRY32,      "AdjacencyEntry"),
    (P32VOID,           "pVirtualRegion"),
  );
  DPH_HEAP_BLOCK64 = iStructureType64.fcCreateClass("DPH_HEAP_BLOCK64",
    UNION (
      (P64VOID,         "pNextAlloc"),                      # PDPH_HEAP_BLOCK
      (LIST_ENTRY64,    "AvailableEntry"),
      (RTL_BALANCED_LINKS64, "TableLinks"),
    ),
    (P64VOID,           "pUserAllocation"),
    (P64VOID,           "pVirtualBlock"),
    (UINT64,            "nVirtualBlockSize"),
    (UINT64,            "nVirtualAccessSize"),
    (UINT64,            "nUserRequestedSize"),
    (UINT64,            "nUserActualSize"),
    (P64VOID,           "UserValue"),
    (UINT64,            "UserFlags"),
    (P64VOID,           "StackTrace"),    #PRTL_TRACE_BLOCK
    (LIST_ENTRY64,      "AdjacencyEntry"),
    (P64VOID,           "pVirtualRegion"),
  );
  # The following values are not used in this case, but since we do not know until
  # after we import them, they must exist but do not need to have a valid value.
  DPH_STATE_ALLOCATED = None;
  DPH_STATE_FREED = None;
# Page heap stores a DPH_ALLOCATION_HEADER structure at the start of the virtual allocation for a heap block.

if not bUseNewPageHeapStructures:
  DPH_ALLOCATION_HEADER32 = iStructureType32.fcCreateClass("DPH_ALLOCATION_HEADER32",
    (ULONG,           "uMarker"),                       # 0xEEEEEEED or 0xEEEEEEEE
    (P32VOID,         "poAllocationInformation"),       # PDPH_HEAP_BLOCK
  );
  DPH_ALLOCATION_HEADER64 = iStructureType64.fcCreateClass("DPH_ALLOCATION_HEADER64",
    (ULONG,           "uMarker"),                       # 0xEEEEEEED or 0xEEEEEEEE
    (ULONG,           "uPadding"),                      # 0xEEEEEEEE or (apparently) 0x00000000
    (P64VOID,         "poAllocationInformation"),       # PDPH_HEAP_BLOCK
  );
else:
  DPH_ALLOCATION_HEADER32 = iStructureType32.fcCreateClass("DPH_ALLOCATION_HEADER32",
    UNION(
      (ULONG,           "uMarker"),                     # 0xEEEEEEED or 0xEEEEEEEE
      (P32VOID,         "poUnknown"),                   # No idea, appears to be close by
    ),
    (P32VOID,         "poAllocationInformation"),       # PDPH_HEAP_BLOCK
  );
  DPH_ALLOCATION_HEADER64 = iStructureType64.fcCreateClass("DPH_ALLOCATION_HEADER64",
    UNION(
      STRUCT(
        (ULONG,           "uMarker"),                   # 0xEEEEEEED or 0xEEEEEEEE
        (ULONG,           "uPadding"),                  # 0xEEEEEEEE or (apparently) 0x00000000
      ),
      (P64VOID,         "poUnknown"),                   # No idea, appears to be close by
    ),
    (P64VOID,         "poAllocationInformation"),       # PDPH_HEAP_BLOCK
  );
auValidPageHeapAllocationHeaderMarkers = [0xEEEEEEED, 0xEEEEEEEE];
auValidPageHeapAllocationHeaderPaddings = [0x0, 0xEEEEEEEE];

# Page heap stores a DPH_BLOCK_INFORMATION structure immediately before every heap block.
# Some information on DPH_BLOCK_INFORMATION can be found here:
# https://msdn.microsoft.com/en-us/library/ms220938(v=vs.90).aspx
# http://www.nirsoft.net/kernel_struct/vista/DPH_BLOCK_INFORMATION.html
DPH_BLOCK_INFORMATION32 = iStructureType32.fcCreateClass("DPH_BLOCK_INFORMATION32",
  (ULONG,           "StartStamp"),
  (P32VOID,         "Heap"),
  (SIZE_T32,        "RequestedSize"),
  (SIZE_T32,        "ActualSize"),
  UNION(
    (LIST_ENTRY32,  "FreeQueue"),
    (SINGLE_LIST_ENTRY32, "FreePushList"),
    (WORD,          "TraceIndex"),
  ),
  (P32VOID,         "StackTrace"),
  (ULONG,           "EndStamp"),
);
DPH_BLOCK_INFORMATION64 = iStructureType64.fcCreateClass("DPH_BLOCK_INFORMATION64",
  (ULONG,           "StartStamp"),
  (ULONG,           "PaddingStart"),
  (P64VOID,         "Heap"),
  (SIZE_T64,        "RequestedSize"),
  (SIZE_T64,        "ActualSize"),
  UNION(
    (LIST_ENTRY64,  "FreeQueue"),
    (SINGLE_LIST_ENTRY64, "FreePushList"),
    (WORD,          "TraceIndex"),
  ),
  (P64VOID,         "StackTrace"),
  (ULONG,           "PaddingEnd"),
  (ULONG,           "EndStamp"),
);
uStartStampAllocated = 0xABCDBBBB;
uStartStampFreed = 0xABCDBBBA;
uEndStampAllocated = 0xDCBABBBB;
uEndStampFreed = 0xDCBABBBA;
uUninitializedHeapBlockFillByte = 0xC0;
uFreedHeapBlockFillByte = 0xF0;
uHeapBlockEndPaddingFillByte = 0xD0;
