import re;

from .mBugReport import cBugReport;
from .ftuLimitedAndAlignedMemoryDumpStartAddressAndSize import ftuLimitedAndAlignedMemoryDumpStartAddressAndSize;
from .mAccessViolation import fUpdateReportForProcessThreadTypeIdAndAddress as fUpdateReportForProcessThreadAccessViolationTypeIdAndAddress;
from .mCP437 import fsCP437HTMLFromString;

dsSecurityImpact_by_sASanBugType = {
  "use-after-poison": "Potentially exploitable security issue",
  "global-buffer-overflow": "Potentially exploitable security issue",
  "heap-use-after-free": "Potentially exploitable security issue",
};

class cASanErrorDetector(object):
  def __init__(oSelf, oCdbWrapper):
    # Hook application stdout output events to detect ASan ERROR messages
    oSelf.oCdbWrapper = oCdbWrapper;
    oCdbWrapper.fAddCallback("Application stderr output", oSelf.__fStdErrOutputCallback);
    oCdbWrapper.fAddCallback("Process terminated", oSelf.__fProcessTerminatedCallback);
    oSelf.__dasStdErr_by_uProcessId = {};
  
  def __fProcessTerminatedCallback(oSelf, oCdbWrapper, oProcess):
    if oProcess.uId in oSelf.__dasStdErr_by_uProcessId:
      del oSelf.__dasStdErr_by_uProcessId[oProcess.uId];
  
  def __fStdErrOutputCallback(oSelf, oCdbWrapper, oConsoleProcess, sLine):
    oSelf.__dasStdErr_by_uProcessId.setdefault(oConsoleProcess.uId, []).append(sLine);
  
  def fAddInformationToBugReport(oSelf, oBugReport, oProcess, oThread):
    # Sample ASan outputs
    # |=================================================================
    # |==1796:1960==ERROR: AddressSanitizer: use-after-poison on address 0x0dd092c4 at pc 0x1aaa90d1 bp 0x0103b8dc sp 0x0103b8d0
    # |READ of size 4 at 0x0dd092c4 thread T0
    # |==1796:1960==WARNING: Failed to use and restart external symbolizer!
    # |==1796:1960==*** WARNING: Failed to initialize DbgHelp!              ***
    # |==1796:1960==*** Most likely this means that the app is already      ***
    # |==1796:1960==*** using DbgHelp, possibly with incompatible flags.    ***
    # |==1796:1960==*** Due to technical reasons, symbolization might crash ***
    # |==1796:1960==*** or produce wrong results.                           ***
    # |    #0 0x1aaa90d0 in blink::Element::setAttribute C:\b\c\b\win_asan_release\src\third_party\WebKit\Source\core\dom\Element.cpp:1326
    # |    #1 0x19dc7c9a in blink::V8Element::idAttributeSetterCallback C:\b\c\b\Win_ASan_Release\src\out\Release\gen\blink\bindings\core\v8\V8Element.cpp:2097
    # |
    # |Address 0x0dd092c4 is a wild pointer.
    # |SUMMARY: AddressSanitizer: use-after-poison C:\b\c\b\win_asan_release\src\third_party\WebKit\Source\core\dom\Element.cpp:1326 in blink::Element::setAttribute
    # |Shadow bytes around the buggy address:
    # |  0x31ba1200: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    # |  0x31ba1210: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    # |  0x31ba1220: 00 00 00 00 00 00 04 f7 f7 f7 f7 f7 f7 f7 f7 f7
    # |  0x31ba1230: f7 f7 f7 f7 f7 f7 f7 f7 f7 f7 f7 f7 f7 f7 f7 f7
    # |  0x31ba1240: f7 f7 f7 f7 f7 f7 f7 f7 f7 f7 f7 f7 f7 f7 f7 f7
    # |=>0x31ba1250: f7 f7 f7 00 00 00 00 04[f7]f7 f7 f7 f7 f7 f7 f7
    # |  0x31ba1260: f7 f7 00 00 00 00 00 00 04 00 00 00 00 04 00 00
    # |  0x31ba1270: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    # |  0x31ba1280: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    # |  0x31ba1290: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    # |  0x31ba12a0: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    # |Shadow byte legend (one shadow byte represents 8 application bytes):
    # |  Addressable:           00
    # |  Partially addressable: 01 02 03 04 05 06 07 
    # |  Heap left redzone:       fa
    # |  Freed heap region:       fd
    # |  Stack left redzone:      f1
    # |  Stack mid redzone:       f2
    # |  Stack right redzone:     f3
    # |  Stack after return:      f5
    # |  Stack use after scope:   f8
    # |  Global redzone:          f9
    # |(704.7a8): Break instruction exception - code 80000003 (first chance)
    # |  Global init order:       f6
    # |  Poisoned by user:        f7
    # |  Container overflow:      fc
    # |  Array cookie:            ac
    # |  Intra object redzone:    bb
    # |  ASan internal:           fe
    # |  Left alloca redzone:     ca
    # |  Right alloca redzone:    cb
    # |==1796:1960==ABORTING
    #############################################################################
    # |=================================================================
    # |==4720:4264==ERROR: AddressSanitizer: global-buffer-overflow on address 0x21a74f3c at pc 0x1601151a bp 0x00efafdc sp 0x00efafd0
    # |READ of size 4 at 0x21a74f3c thread T0
    # |==4720:4264==WARNING: Failed to use and restart external symbolizer!
    # |==4720:4264==*** WARNING: Failed to initialize DbgHelp!              ***
    # |==4720:4264==*** Most likely this means that the app is already      ***
    # |==4720:4264==*** using DbgHelp, possibly with incompatible flags.    ***
    # |==4720:4264==*** Due to technical reasons, symbolization might crash ***
    # |==4720:4264==*** or produce wrong results.                           ***
    # |    #0 0x16011519 in blink::ElementData::Attributes C:\b\c\b\win_asan_release\src\third_party\WebKit\Source\core\dom\ElementData.h:200
    # |    #1 0x1a9a8bcd in blink::Element::setAttribute C:\b\c\b\win_asan_release\src\third_party\WebKit\Source\core\dom\Element.cpp:1322
    # |    #2 0x19cc7c9a in blink::V8Element::idAttributeSetterCallback C:\b\c\b\Win_ASan_Release\src\out\Release\gen\blink\bindings\core\v8\V8Element.cpp:2097
    # |
    # |0x21a74f3c is located 36 bytes to the left of global variable 'WTF::g_global_empty16_bitStorage' defined in '../../third_party/WebKit/Source/platform/wtf/text/StringImpl.cpp:166:1' (0x21a74f60) of size 12
    # |0x21a74f3c is located 16 bytes to the right of global variable 'WTF::g_global_emptyStorage' defined in '../../third_party/WebKit/Source/platform/wtf/text/StringImpl.cpp:165:1' (0x21a74f20) of size 12
    # |SUMMARY: AddressSanitizer: global-buffer-overflow C:\b\c\b\win_asan_release\src\third_party\WebKit\Source\core\dom\ElementData.h:200 in blink::ElementData::Attributes
    # |Shadow bytes around the buggy address:
    # |  0x3434e990: f9 f9 f9 f9 04 f9 f9 f9 f9 f9 f9 f9 04 f9 f9 f9
    # |  0x3434e9a0: f9 f9 f9 f9 00 f9 f9 f9 f9 f9 f9 f9 04 f9 f9 f9
    # |  0x3434e9b0: f9 f9 f9 f9 04 f9 f9 f9 f9 f9 f9 f9 00 f9 f9 f9
    # |  0x3434e9c0: f9 f9 f9 f9 04 f9 f9 f9 f9 f9 f9 f9 00 04 f9 f9
    # |  0x3434e9d0: f9 f9 f9 f9 04 f9 f9 f9 f9 f9 f9 f9 04 f9 f9 f9
    # |=>0x3434e9e0: f9 f9 f9 f9 00 04 f9[f9]f9 f9 f9 f9 00 04 f9 f9
    # |  0x3434e9f0: f9 f9 f9 f9 00 00 f9 f9 f9 f9 f9 f9 04 f9 f9 f9
    # |  0x3434ea00: f9 f9 f9 f9 04 f9 f9 f9 f9 f9 f9 f9 04 f9 f9 f9
    # |  0x3434ea10: f9 f9 f9 f9 04 f9 f9 f9 f9 f9 f9 f9 04 f9 f9 f9
    # |  0x3434ea20: f9 f9 f9 f9 04 f9 f9 f9 f9 f9 f9 f9 04 f9 f9 f9
    # |  0x3434ea30: f9 f9 f9 f9 04 f9 f9 f9 f9 f9 f9 f9 04 f9 f9 f9
    # |Shadow byte legend (one shadow byte represents 8 application bytes):
    # |  Addressable:           00
    # |  Partially addressable: 01 02 03 04 05 06 07
    # |  Heap left redzone:       fa
    # |  Freed heap region:       fd
    # |  Stack left redzone:      f1
    # |  Stack mid redzone:       f2
    # |  Stack right redzone:     f3
    # |  Stack after return:      f5
    # |  Stack use after scope:   f8
    # |  Global redzone:          f9
    # |  Global init order:       f6
    # |  Poisoned by user:        f7
    # |  Container overflow:      fc
    # |  Array cookie:            ac
    # |  Intra object redzone:    bb
    # |  ASan internal:           fe
    # |  Left alloca redzone:     ca
    # |  Right alloca redzone:    cb
    # |==4720:4264==ABORTING
    ##############################################################################
    # |=================================================================
    # |==3012:3984==ERROR: AddressSanitizer: heap-use-after-free on address 0x0636d770 at pc 0x14e45df9 bp 0x00c9a7c8 sp 0x00c9a7bc
    # |READ of size 1 at 0x0636d770 thread T0
    # |    #0 0x14e45df8 in std::_Hash<std::_Uset_traits<device::BluetoothAdapter::Observer *,std::_Uhash_compare<device::BluetoothAdapter::Observer *,std::hash<device::BluetoothAdapter::Observer *>,std::equal_to<device::BluetoothAdapter::Observer *> >,std::allocator<device::BluetoothAdapter::Observer *>,0> >::equal_range c:\b\c\win_toolchain\vs_files\f53e4598951162bad6330f7a167486c7ae5db1e5\vc\include\xhash:636
    # |    #1 0x15142422 in std::_Hash<std::_Umap_traits<int,ui::AXPlatformNode *,std::_Uhash_compare<int,base_hash::hash<int>,std::equal_to<int> >,std::allocator<std::pair<const int,ui::AXPlatformNode *> >,0> >::erase c:\b\c\win_toolchain\vs_files\f53e4598951162bad6330f7a167486c7ae5db1e5\vc\include\xhash:563
    # |    #2 0x15147750 in ui::AXPlatformNodeWin::Destroy C:\b\c\b\win_asan_release\src\ui\accessibility\platform\ax_platform_node_win.cc:556
    # |    #3 0x10529055 in content::BrowserAccessibilityWin::~BrowserAccessibilityWin C:\b\c\b\win_asan_release\src\content\browser\accessibility\browser_accessibility_win.h:29
    # |    #4 0x104c9fba in content::BrowserAccessibility::NativeReleaseReference C:\b\c\b\win_asan_release\src\content\browser\accessibility\browser_accessibility.cc:556
    # |    #5 0x1051014c in content::BrowserAccessibilityManager::OnNodeWillBeDeleted C:\b\c\b\win_asan_release\src\content\browser\accessibility\browser_accessibility_manager.cc:1134
    # |    #6 0x15116137 in ui::AXTree::DestroyNodeAndSubtree C:\b\c\b\win_asan_release\src\ui\accessibility\ax_tree.cc:501
    # |    #7 0x15119afb in ui::AXTree::DestroySubtree C:\b\c\b\win_asan_release\src\ui\accessibility\ax_tree.cc:494
    # |    #8 0x1511a03b in ui::AXTree::UpdateNode C:\b\c\b\win_asan_release\src\ui\accessibility\ax_tree.cc:406
    # |    #9 0x15117cb9 in ui::AXTree::Unserialize C:\b\c\b\win_asan_release\src\ui\accessibility\ax_tree.cc:258
    # |    #10 0x1050c39b in content::BrowserAccessibilityManager::OnAccessibilityEvents C:\b\c\b\win_asan_release\src\content\browser\accessibility\browser_accessibility_manager.cc:364
    # |    #11 0x10b436b5 in content::RenderFrameHostImpl::OnAccessibilityEvents C:\b\c\b\win_asan_release\src\content\browser\frame_host\render_frame_host_impl.cc:2388
    # |    #12 0x10b427af in IPC::MessageT<AccessibilityHostMsg_Events_Meta,std::tuple<std::vector<AccessibilityHostMsg_EventParams,std::allocator<AccessibilityHostMsg_EventParams> >,int,int>,void>::Dispatch<content::RenderFrameHostImpl,content::RenderFrameHostImpl,void,void (content::RenderFrameHostImpl::*)(const std::vector<AccessibilityHostMsg_EventParams,std::allocator<AccessibilityHostMsg_EventParams> > &, int, int) __attribute__((thiscall))> C:\b\c\b\win_asan_release\src\ipc\ipc_message_templates.h:120
    # |    #13 0x10b23853 in content::RenderFrameHostImpl::OnMessageReceived C:\b\c\b\win_asan_release\src\content\browser\frame_host\render_frame_host_impl.cc:890
    # |    #14 0x11183345 in content::RenderProcessHostImpl::OnMessageReceived C:\b\c\b\win_asan_release\src\content\browser\renderer_host\render_process_host_impl.cc:2831
    # |    #15 0x145f0109 in IPC::ChannelProxy::Context::OnDispatchMessage C:\b\c\b\win_asan_release\src\ipc\ipc_channel_proxy.cc:329
    # |    #16 0x1153d5fe in base::internal::Invoker<base::internal::BindState<base::internal::IgnoreResultHelper<bool (content::UtilityProcessHostClient::*)(const IPC::Message &) __attribute__((thiscall))>,scoped_refptr<content::UtilityProcessHostClient>,IPC::Message>,void ()>::Run C:\b\c\b\win_asan_release\src\base\bind_internal.h:317
    # |    #17 0x1291b01a in base::debug::TaskAnnotator::RunTask C:\b\c\b\win_asan_release\src\base\debug\task_annotator.cc:57
    # |    #18 0x12762259 in base::MessageLoop::RunTask C:\b\c\b\win_asan_release\src\base\message_loop\message_loop.cc:422
    # |    #19 0x1276363b in base::MessageLoop::DeferOrRunPendingTask C:\b\c\b\win_asan_release\src\base\message_loop\message_loop.cc:433
    # |    #20 0x127642f3 in base::MessageLoop::DoWork C:\b\c\b\win_asan_release\src\base\message_loop\message_loop.cc:540
    # |    #21 0x12920256 in base::MessagePumpForUI::DoRunLoop C:\b\c\b\win_asan_release\src\base\message_loop\message_pump_win.cc:173
    # |    #22 0x1291f155 in base::MessagePumpWin::Run C:\b\c\b\win_asan_release\src\base\message_loop\message_pump_win.cc:56
    # |    #23 0x12760ec4 in base::MessageLoop::Run C:\b\c\b\win_asan_release\src\base\message_loop\message_loop.cc:369
    # |    #24 0x1283d5ed in base::RunLoop::Run C:\b\c\b\win_asan_release\src\base\run_loop.cc:111
    # |    #25 0x123ef3d1 in ChromeBrowserMainParts::MainMessageLoopRun C:\b\c\b\win_asan_release\src\chrome\browser\chrome_browser_main.cc:1967
    # |    #26 0x107205e4 in content::BrowserMainLoop::RunMainMessageLoopParts C:\b\c\b\win_asan_release\src\content\browser\browser_main_loop.cc:1170
    # |    #27 0x10729dfd in content::BrowserMainRunnerImpl::Run C:\b\c\b\win_asan_release\src\content\browser\browser_main_runner.cc:142
    # |    #28 0x107133b9 in content::BrowserMain C:\b\c\b\win_asan_release\src\content\browser\browser_main.cc:46
    # |    #29 0x1211d5d6 in content::RunNamedProcessTypeMain C:\b\c\b\win_asan_release\src\content\app\content_main_runner.cc:408
    # |    #30 0x1211e95d in content::ContentMainRunnerImpl::Run C:\b\c\b\win_asan_release\src\content\app\content_main_runner.cc:687
    # |    #31 0x12189d05 in service_manager::Main C:\b\c\b\win_asan_release\src\services\service_manager\embedder\main.cc:469
    # |    #32 0x1211d2cc in content::ContentMain C:\b\c\b\win_asan_release\src\content\app\content_main.cc:19
    # |    #33 0xf961320 in ChromeMain C:\b\c\b\win_asan_release\src\chrome\app\chrome_main.cc:139
    # |    #34 0xdb9f24 in MainDllLoader::Launch C:\b\c\b\win_asan_release\src\chrome\app\main_dll_loader_win.cc:199
    # |    #35 0xdb1c53 in main C:\b\c\b\win_asan_release\src\chrome\app\chrome_exe_main_win.cc:268
    # |    #36 0x111f72a in __scrt_common_main_seh f:\dd\vctools\crt\vcstartup\src\startup\exe_common.inl:253
    # |    #37 0x74b39ba3 in BaseThreadInitThunk+0x23 (C:\Windows\System32\KERNEL32.DLL+0x68919ba3)
    # |    #38 0x76fcac9a in RtlCheckRegistryKey+0xfba (C:\Windows\SYSTEM32\ntdll.dll+0x6a26ac9a)
    # |    #39 0x76fcac6e in RtlCheckRegistryKey+0xf8e (C:\Windows\SYSTEM32\ntdll.dll+0x6a26ac6e)
    # |
    # |0x0636d770 is located 64 bytes inside of 140-byte region [0x0636d730,0x0636d7bc)
    # |freed by thread T0 here:
    # |    #0 0x110e378 in free e:\b\build\slave\win_upload_clang\build\src\third_party\llvm\projects\compiler-rt\lib\asan\asan_malloc_win.cc:44
    # |    #1 0x105296f9 in ATL::CComObject<content::BrowserAccessibilityComWin>::`vector deleting destructor' c:\b\c\win_toolchain\vs_files\f53e4598951162bad6330f7a167486c7ae5db1e5\vc\atlmfc\include\atlcom.h
    # |    #2 0x1515b6fb in ATL::CComObject<ui::AXPlatformNodeWin>::Release c:\b\c\win_toolchain\vs_files\f53e4598951162bad6330f7a167486c7ae5db1e5\vc\atlmfc\include\atlcom.h:2934
    # |    #3 0x1514765e in ui::AXPlatformNodeWin::Dispose C:\b\c\b\win_asan_release\src\ui\accessibility\platform\ax_platform_node_win.cc:550
    # |    #4 0x15147707 in ui::AXPlatformNodeWin::Destroy C:\b\c\b\win_asan_release\src\ui\accessibility\platform\ax_platform_node_win.cc:555
    # |    #5 0x10529055 in content::BrowserAccessibilityWin::~BrowserAccessibilityWin C:\b\c\b\win_asan_release\src\content\browser\accessibility\browser_accessibility_win.h:29
    # |    #6 0x104c9fba in content::BrowserAccessibility::NativeReleaseReference C:\b\c\b\win_asan_release\src\content\browser\accessibility\browser_accessibility.cc:556
    # |    #7 0x1051014c in content::BrowserAccessibilityManager::OnNodeWillBeDeleted C:\b\c\b\win_asan_release\src\content\browser\accessibility\browser_accessibility_manager.cc:1134
    # |    #8 0x15116137 in ui::AXTree::DestroyNodeAndSubtree C:\b\c\b\win_asan_release\src\ui\accessibility\ax_tree.cc:501
    # |    #9 0x15119afb in ui::AXTree::DestroySubtree C:\b\c\b\win_asan_release\src\ui\accessibility\ax_tree.cc:494
    # |    #10 0x1511a03b in ui::AXTree::UpdateNode C:\b\c\b\win_asan_release\src\ui\accessibility\ax_tree.cc:406
    # |    #11 0x15117cb9 in ui::AXTree::Unserialize C:\b\c\b\win_asan_release\src\ui\accessibility\ax_tree.cc:258
    # |    #12 0x1050c39b in content::BrowserAccessibilityManager::OnAccessibilityEvents C:\b\c\b\win_asan_release\src\content\browser\accessibility\browser_accessibility_manager.cc:364
    # |    #13 0x10b436b5 in content::RenderFrameHostImpl::OnAccessibilityEvents C:\b\c\b\win_asan_release\src\content\browser\frame_host\render_frame_host_impl.cc:2388
    # |    #14 0x10b427af in IPC::MessageT<AccessibilityHostMsg_Events_Meta,std::tuple<std::vector<AccessibilityHostMsg_EventParams,std::allocator<AccessibilityHostMsg_EventParams> >,int,int>,void>::Dispatch<content::RenderFrameHostImpl,content::RenderFrameHostImpl,void,void (content::RenderFrameHostImpl::*)(const std::vector<AccessibilityHostMsg_EventParams,std::allocator<AccessibilityHostMsg_EventParams> > &, int, int) __attribute__((thiscall))> C:\b\c\b\win_asan_release\src\ipc\ipc_message_templates.h:120
    # |    #15 0x10b23853 in content::RenderFrameHostImpl::OnMessageReceived C:\b\c\b\win_asan_release\src\content\browser\frame_host\render_frame_host_impl.cc:890
    # |    #16 0x11183345 in content::RenderProcessHostImpl::OnMessageReceived C:\b\c\b\win_asan_release\src\content\browser\renderer_host\render_process_host_impl.cc:2831
    # |    #17 0x145f0109 in IPC::ChannelProxy::Context::OnDispatchMessage C:\b\c\b\win_asan_release\src\ipc\ipc_channel_proxy.cc:329
    # |    #18 0x1153d5fe in base::internal::Invoker<base::internal::BindState<base::internal::IgnoreResultHelper<bool (content::UtilityProcessHostClient::*)(const IPC::Message &) __attribute__((thiscall))>,scoped_refptr<content::UtilityProcessHostClient>,IPC::Message>,void ()>::Run C:\b\c\b\win_asan_release\src\base\bind_internal.h:317
    # |    #19 0x1291b01a in base::debug::TaskAnnotator::RunTask C:\b\c\b\win_asan_release\src\base\debug\task_annotator.cc:57
    # |    #20 0x12762259 in base::MessageLoop::RunTask C:\b\c\b\win_asan_release\src\base\message_loop\message_loop.cc:422
    # |    #21 0x1276363b in base::MessageLoop::DeferOrRunPendingTask C:\b\c\b\win_asan_release\src\base\message_loop\message_loop.cc:433
    # |    #22 0x127642f3 in base::MessageLoop::DoWork C:\b\c\b\win_asan_release\src\base\message_loop\message_loop.cc:540
    # |    #23 0x12920256 in base::MessagePumpForUI::DoRunLoop C:\b\c\b\win_asan_release\src\base\message_loop\message_pump_win.cc:173
    # |    #24 0x1291f155 in base::MessagePumpWin::Run C:\b\c\b\win_asan_release\src\base\message_loop\message_pump_win.cc:56
    # |    #25 0x12760ec4 in base::MessageLoop::Run C:\b\c\b\win_asan_release\src\base\message_loop\message_loop.cc:369
    # |    #26 0x1283d5ed in base::RunLoop::Run C:\b\c\b\win_asan_release\src\base\run_loop.cc:111
    # |    #27 0x123ef3d1 in ChromeBrowserMainParts::MainMessageLoopRun C:\b\c\b\win_asan_release\src\chrome\browser\chrome_browser_main.cc:1967
    # |    #28 0x107205e4 in content::BrowserMainLoop::RunMainMessageLoopParts C:\b\c\b\win_asan_release\src\content\browser\browser_main_loop.cc:1170
    # |
    # |previously allocated by thread T0 here:
    # |    #0 0x110e45c in malloc e:\b\build\slave\win_upload_clang\build\src\third_party\llvm\projects\compiler-rt\lib\asan\asan_malloc_win.cc:60
    # |    #1 0x19f475bb in operator new f:\dd\vctools\crt\vcstartup\src\heap\new_scalar.cpp:19
    # |    #2 0x19f47cae in operator new f:\dd\vctools\crt\vcstartup\src\heap\new_scalar_nothrow.cpp:17
    # |    #3 0x10528bf2 in ATL::CComObject<content::BrowserAccessibilityComWin>::CreateInstance c:\b\c\win_toolchain\vs_files\f53e4598951162bad6330f7a167486c7ae5db1e5\vc\atlmfc\include\atlcom.h:2966
    # |    #4 0x10528a2f in content::BrowserAccessibilityWin::BrowserAccessibilityWin C:\b\c\b\win_asan_release\src\content\browser\accessibility\browser_accessibility_win.cc:19
    # |    #5 0x10528962 in content::BrowserAccessibility::Create C:\b\c\b\win_asan_release\src\content\browser\accessibility\browser_accessibility_win.cc:14
    # |    #6 0x10510613 in content::BrowserAccessibilityManager::OnNodeCreated C:\b\c\b\win_asan_release\src\content\browser\accessibility\browser_accessibility_manager.cc:1166
    # |    #7 0x105261e3 in content::BrowserAccessibilityManagerWin::OnNodeCreated C:\b\c\b\win_asan_release\src\content\browser\accessibility\browser_accessibility_manager_win.cc:249
    # |    #8 0x1511ac76 in ui::AXTree::CreateNode C:\b\c\b\win_asan_release\src\ui\accessibility\ax_tree.cc:330
    # |    #9 0x15119dda in ui::AXTree::UpdateNode C:\b\c\b\win_asan_release\src\ui\accessibility\ax_tree.cc:360
    # |    #10 0x15117cb9 in ui::AXTree::Unserialize C:\b\c\b\win_asan_release\src\ui\accessibility\ax_tree.cc:258
    # |    #11 0x1050a873 in content::BrowserAccessibilityManager::Initialize C:\b\c\b\win_asan_release\src\content\browser\accessibility\browser_accessibility_manager.cc:177
    # |    #12 0x105250e4 in content::BrowserAccessibilityManagerWin::BrowserAccessibilityManagerWin C:\b\c\b\win_asan_release\src\content\browser\accessibility\browser_accessibility_manager_win.cc:44
    # |    #13 0x11234704 in content::RenderWidgetHostViewAura::CreateBrowserAccessibilityManager C:\b\c\b\win_asan_release\src\content\browser\renderer_host\render_widget_host_view_aura.cc:1144
    # |    #14 0x10b5a82a in content::RenderFrameHostImpl::GetOrCreateBrowserAccessibilityManager C:\b\c\b\win_asan_release\src\content\browser\frame_host\render_frame_host_impl.cc:3595
    # |(bc4.f90): Break instruction exception - code 80000003 (first chance)
    # |    #15 0x10b42c8a in content::RenderFrameHostImpl::OnAccessibilityEvents C:\b\c\b\win_asan_release\src\content\browser\frame_host\render_frame_host_impl.cc:2360
    # |    #16 0x10b427af in IPC::MessageT<AccessibilityHostMsg_Events_Meta,std::tuple<std::vector<AccessibilityHostMsg_EventParams,std::allocator<AccessibilityHostMsg_EventParams> >,int,int>,void>::Dispatch<content::RenderFrameHostImpl,content::RenderFrameHostImpl,void,void (content::RenderFrameHostImpl::*)(const std::vector<AccessibilityHostMsg_EventParams,std::allocator<AccessibilityHostMsg_EventParams> > &, int, int) __attribute__((thiscall))> C:\b\c\b\win_asan_release\src\ipc\ipc_message_templates.h:120
    # |    #17 0x10b23853 in content::RenderFrameHostImpl::OnMessageReceived C:\b\c\b\win_asan_release\src\content\browser\frame_host\render_frame_host_impl.cc:890
    # |    #18 0x11183345 in content::RenderProcessHostImpl::OnMessageReceived C:\b\c\b\win_asan_release\src\content\browser\renderer_host\render_process_host_impl.cc:2831
    # |    #19 0x145f0109 in IPC::ChannelProxy::Context::OnDispatchMessage C:\b\c\b\win_asan_release\src\ipc\ipc_channel_proxy.cc:329
    # |    #20 0x1153d5fe in base::internal::Invoker<base::internal::BindState<base::internal::IgnoreResultHelper<bool (content::UtilityProcessHostClient::*)(const IPC::Message &) __attribute__((thiscall))>,scoped_refptr<content::UtilityProcessHostClient>,IPC::Message>,void ()>::Run C:\b\c\b\win_asan_release\src\base\bind_internal.h:317
    # |    #21 0x1291b01a in base::debug::TaskAnnotator::RunTask C:\b\c\b\win_asan_release\src\base\debug\task_annotator.cc:57
    # |    #22 0x12762259 in base::MessageLoop::RunTask C:\b\c\b\win_asan_release\src\base\message_loop\message_loop.cc:422
    # |    #23 0x1276363b in base::MessageLoop::DeferOrRunPendingTask C:\b\c\b\win_asan_release\src\base\message_loop\message_loop.cc:433
    # |    #24 0x127642f3 in base::MessageLoop::DoWork C:\b\c\b\win_asan_release\src\base\message_loop\message_loop.cc:540
    # |    #25 0x12920256 in base::MessagePumpForUI::DoRunLoop C:\b\c\b\win_asan_release\src\base\message_loop\message_pump_win.cc:173
    # |    #26 0x1291f155 in base::MessagePumpWin::Run C:\b\c\b\win_asan_release\src\base\message_loop\message_pump_win.cc:56
    # |    #27 0x12760ec4 in base::MessageLoop::Run C:\b\c\b\win_asan_release\src\base\message_loop\message_loop.cc:369
    # |    #28 0x1283d5ed in base::RunLoop::Run C:\b\c\b\win_asan_release\src\base\run_loop.cc:111
    # |
    # |SUMMARY: AddressSanitizer: heap-use-after-free c:\b\c\win_toolchain\vs_files\f53e4598951162bad6330f7a167486c7ae5db1e5\vc\include\xhash:636 in std::_Hash<std::_Uset_traits<device::BluetoothAdapter::Observer *,std::_Uhash_compare<device::BluetoothAdapter::Observer *,std::hash<device::BluetoothAdapter::Observer *>,std::equal_to<device::BluetoothAdapter::Observer *> >,std::allocator<device::BluetoothAdapter::Observer *>,0> >::equal_range
    # |Shadow bytes around the buggy address:
    # |  0x30c6da90: fa fa fa fa fa fa fa fa 00 00 00 00 00 00 00 00
    # |  0x30c6daa0: 00 00 00 00 00 00 00 00 00 04 fa fa fa fa fa fa
    # |  0x30c6dab0: fa fa fd fd fd fd fd fd fd fd fd fd fd fd fd fd
    # |  0x30c6dac0: fd fd fd fd fa fa fa fa fa fa fa fa 00 00 00 00
    # |  0x30c6dad0: 00 00 00 00 00 00 00 00 00 00 00 00 00 04 fa fa
    # |=>0x30c6dae0: fa fa fa fa fa fa fd fd fd fd fd fd fd fd[fd]fd
    # |  0x30c6daf0: fd fd fd fd fd fd fd fd fa fa fa fa fa fa fa fa
    # |  0x30c6db00: fd fd fd fd fd fd fd fd fd fd fd fd fd fd fd fd
    # |  0x30c6db10: fd fd fa fa fa fa fa fa fa fa fd fd fd fd fd fd
    # |  0x30c6db20: fd fd fd fd fd fd fd fd fd fd fd fd fa fa fa fa
    # |  0x30c6db30: fa fa fa fa 00 00 00 00 00 00 00 00 00 00 00 00
    # |Shadow byte legend (one shadow byte represents 8 application bytes):
    # |  Addressable:           00
    # |  Partially addressable: 01 02 03 04 05 06 07 
    # |  Heap left redzone:       fa
    # |  Freed heap region:       fd
    # |  Stack left redzone:      f1
    # |  Stack mid redzone:       f2
    # |  Stack right redzone:     f3
    # |  Stack after return:      f5
    # |  Stack use after scope:   f8
    # |  Global redzone:          f9
    # |  Global init order:       f6
    # |  Poisoned by user:        f7
    # |  Container overflow:      fc
    # |  Array cookie:            ac
    # |  Intra object redzone:    bb
    # |  ASan internal:           fe
    # |  Left alloca redzone:     ca
    # |  Right alloca redzone:    cb
    # |==3012:3984==ABORTING
    ##############################################################################
    # |=================================================================
    # |==1484==ERROR: AddressSanitizer: access-violation on unknown address 0x000000000058 (pc 0x7ff8e25139aa bp 0x00d4c7df31d0 sp 0x00d4c7df2e00 T0)
    # |==1484==The signal is caused by a READ memory access.
    # |==1484==Hint: address points to the zero page.
    # |==1484==*** WARNING: Failed to initialize DbgHelp!              ***
    # |==1484==*** Most likely this means that the app is already      ***
    # |==1484==*** using DbgHelp, possibly with incompatible flags.    ***
    # |==1484==*** Due to technical reasons, symbolization might crash ***
    # |==1484==*** or produce wrong results.                           ***
    # |    #0 0x7ff8e25139a9 in blink::Element::setAttribute(class blink::QualifiedName const &,class WTF::AtomicString const &) C:\b\c\b\win_asan_release\src\third_party\WebKit\Source\core\dom\Element.cpp:1341
    # |    #1 0x7ff8e2511a8c in blink::Element::SetIntegralAttribute(class blink::QualifiedName const &,int) C:\b\c\b\win_asan_release\src\third_party\WebKit\Source\core\dom\Element.cpp:3877:3
    # |    #2 0x7ff8e24d9144 in blink::Document::WillChangeFrameOwnerProperties(int,int,enum blink::ScrollbarMode,bool) C:\b\c\b\win_asan_release\src\third_party\WebKit\Source\core\dom\Document.cpp:5040:13
    # |    #3 0x7ff8e287de2c in blink::HTMLFrameElementBase::SetMarginWidth(int) C:\b\c\b\win_asan_release\src\third_party\WebKit\Source\core\html\HTMLFrameElementBase.cpp:275:24
    # |    #4 0x7ff8e287ce7c in blink::HTMLFrameElementBase::ParseAttribute(struct blink::Element::AttributeModificationParams const &) C:\b\c\b\win_asan_release\src\third_party\WebKit\Source\core\html\HTMLFrameElementBase.cpp:146:5
    # |    #5 0x7ff8e2863a1c in blink::HTMLIFrameElement::ParseAttribute(struct blink::Element::AttributeModificationParams const &) C:\b\c\b\win_asan_release\src\third_party\WebKit\Source\core\html\HTMLIFrameElement.cpp:212:27
    # |    #6 0x7ff8e25252b2 in blink::Element::AttributeChanged(struct blink::Element::AttributeModificationParams const &) C:\b\c\b\win_asan_release\src\third_party\WebKit\Source\core\dom\Element.cpp:1429:3
    # |    #7 0x7ff8de5f2722 in blink::HTMLElement::AttributeChanged(struct blink::Element::AttributeModificationParams const &) C:\b\c\b\win_asan_release\src\third_party\WebKit\Source\core\html\HTMLElement.cpp:559:12
    # |    #8 0x7ff8e253c148 in blink::Element::DidAddAttribute(class blink::QualifiedName const &,class WTF::AtomicString const &) C:\b\c\b\win_asan_release\src\third_party\WebKit\Source\core\dom\Element.cpp:4102:3
    # |    #9 0x7ff8e253b9f7 in blink::Element::AppendAttributeInternal(class blink::QualifiedName const &,class WTF::AtomicString const &,enum blink::Element::SynchronizationOfLazyAttribute) C:\b\c\b\win_asan_release\src\third_party\WebKit\Source\core\dom\Element.cpp:2827:5
    # |    #10 0x7ff8e2513ddc in blink::Element::setAttribute(class blink::QualifiedName const &,class WTF::AtomicString const &) C:\b\c\b\win_asan_release\src\third_party\WebKit\Source\core\dom\Element.cpp:1343:18
    # |    #11 0x7ff8e1bde3cd in blink::V8HTMLIFrameElement::marginWidthAttributeSetterCallback(class v8::FunctionCallbackInfo<class v8::Value> const &) C:\b\c\b\win_asan_release\src\out\release_x64\gen\blink\bindings\core\v8\V8HTMLIFrameElement.cpp:860:3
    # |    #12 0x7ff8d7b902ea in v8::internal::FunctionCallbackArguments::Call(void (*)(class v8::FunctionCallbackInfo<class v8::Value> const &)) C:\b\c\b\win_asan_release\src\v8\src\api-arguments.cc:26:3
    # |    #13 0x7ff8d7dc1950 in v8::internal::`anonymous namespace'::HandleApiCallHelper<0> C:\b\c\b\win_asan_release\src\v8\src\builtins\builtins-api.cc:112:36
    # |    #14 0x7ff8d7dbf2a6 in v8::internal::Builtins::InvokeApiFunction(class v8::internal::Isolate *,bool,class v8::internal::Handle<class v8::internal::HeapObject>,class v8::internal::Handle<class v8::internal::Object>,int,class v8::internal::Handle<class v8::internal::Object> * const,class v8::internal::Handle<class v8::internal::HeapObject>) C:\b\c\b\win_asan_release\src\v8\src\builtins\builtins-api.cc:220:16
    # |    #15 0x7ff8d8cccfbe in v8::internal::Object::SetPropertyWithAccessor(class v8::internal::LookupIterator *,class v8::internal::Handle<class v8::internal::Object>,enum v8::internal::ShouldThrow) C:\b\c\b\win_asan_release\src\v8\src\objects.cc:1753:5
    # |    #16 0x7ff8d8d129e4 in v8::internal::Object::SetPropertyInternal(class v8::internal::LookupIterator *,class v8::internal::Handle<class v8::internal::Object>,enum v8::internal::LanguageMode,enum v8::internal::Object::StoreFromKeyed,bool *) C:\b\c\b\win_asan_release\src\v8\src\objects.cc:4875:16
    # |    #17 0x7ff8d8d12045 in v8::internal::Object::SetProperty(class v8::internal::LookupIterator *,class v8::internal::Handle<class v8::internal::Object>,enum v8::internal::LanguageMode,enum v8::internal::Object::StoreFromKeyed) C:\b\c\b\win_asan_release\src\v8\src\objects.cc:4907:9
    # |    #18 0x7ff8d8a57cc0 in v8::internal::StoreIC::Store(class v8::internal::Handle<class v8::internal::Object>,class v8::internal::Handle<class v8::internal::Name>,class v8::internal::Handle<class v8::internal::Object>,enum v8::internal::Object::StoreFromKeyed) C:\b\c\b\win_asan_release\src\v8\src\ic\ic.cc:1388:3
    # |    #19 0x7ff8d8a6e8c6 in v8::internal::Runtime_StoreIC_Miss(int,class v8::internal::Object * *,class v8::internal::Isolate *) C:\b\c\b\win_asan_release\src\v8\src\ic\ic.cc:2182:1
    # |    #20 0xd13bd043a0  (<unknown module>)
    # |    #21 0xd4c7df5dcf  (<unknown module>)
    # |    #22 0x7ff8d9163c0e in v8::internal::Runtime_IsJSWeakSet(int,class v8::internal::Object * *,class v8::internal::Isolate *) C:\b\c\b\win_asan_release\src\v8\src\runtime\runtime-compiler.cc:21
    # |    #23 0x12e9849e3bf0  (<unknown module>)
    # |    #24 0x1df97082200  (<unknown module>)
    # |    #25 0x284123bebef  (<unknown module>)
    # |    #26 0x14a78046a40  (<unknown module>)
    # |    #27 0xd13bd042e0  (<unknown module>)
    # |    #28 0xd4c7df5cdf  (<unknown module>)
    # |    #29 0x5  (<unknown module>)
    # |    #30 0xd4c7df5d7f  (<unknown module>)
    # |    #31 0xd13bd882c0  (<unknown module>)
    # |    #32 0x12e9849e34f0  (<unknown module>)
    # |    #33 0x11a2a705340  (<unknown module>)
    # |    #34 0x12e9885660a0  (<unknown module>)
    # |    #35 0x1ffffffff  (<unknown module>)
    # |    #36 0x111b1037048  (<unknown module>)
    # |    #37 0x40  (<unknown module>)
    # |    #38 0xd4c7df5db7  (<unknown module>)
    # |    #39 0x12af79401d0f  (<unknown module>)
    # |    #40 0x17  (<unknown module>)
    # |    #41 0xd4c7df5db7  (<unknown module>)
    # |    #42 0xd13bd1359c  (<unknown module>)
    # |    #43 0x11a2a705340  (<unknown module>)
    # |    #44 0x40ffffffff  (<unknown module>)
    # |    #45 0x12e988566038  (<unknown module>)
    # |    #46 0x12e9849e3bf0  (<unknown module>)
    # |    #47 0x1df97082200  (<unknown module>)
    # |    #48 0xd4c7df5def  (<unknown module>)
    # |    #49 0xd13bd0c1e2  (<unknown module>)
    # |    #50 0x11a2a7531f0  (<unknown module>)
    # |
    # |AddressSanitizer can not provide additional info.
    # |SUMMARY: AddressSanitizer: access-violation C:\b\c\b\win_asan_release\src\third_party\WebKit\Source\core\dom\Element.cpp:1341 in blink::Element::setAttribute(class blink::QualifiedName const &,class WTF::AtomicString const &)
    # |==1484==ABORTING
    
    # |==4016==AddressSanitizer's allocator is terminating the process instead of returning 0
    
    # |==4916==ERROR: AddressSanitizer failed to allocate 0x08000000 (134217728) bytes at 0x38000000 (error code: 1455)
    
    # |==4824==ERROR: AddressSanitizer failed to allocate 0x10000 (65536) bytes of stack depot (error code: 1455)
    
    # |==6824==ERROR: AddressSanitizer failed to allocate aligned 0x100000 (1048576) bytes of SizeClassAllocator32 (error code: 1455)
    
    # The ASan error message may be shown from the main process, rather than the process that triggered it. So, we will
    # scan all output for an error reported in oProcess
    for asOutput in oSelf.__dasStdErr_by_uProcessId.values():
      for uStartIndex in range(len(asOutput) - 1):
        sLine = asOutput[uStartIndex];
        # Check for OOM report:
        oAllocatorFailMatch = re.match(
          r"^("
            r"==(\d+)==AddressSanitizer's allocator is terminating the process instead of returning 0"
          r"|"
            r"==(\d+)==ERROR: AddressSanitizer failed to allocate( aligned)? 0x[0-9`a-f]+ \(\d+\) bytes "
                r"(at 0x[0-9`a-f]+|of( \w+)+) \(error code: 1455\)"
          r")\s*$",
          sLine,
          re.I,
        );
        if oAllocatorFailMatch:
          # The process in which the OOM crash happened may not be the process in which it is reported.
          oBugReport.s0BugTypeId = "OOM";
          oBugReport.s0BugDescription = "ASan triggered a breakpoint to indicate it was unable to allocate enough memory.";
          oBugReport.s00SecurityImpact = None;
          return;
        # Check for memory corruption report:
        oSummaryMatch = re.match(
          r"^"
          r"==(\d+)==ERROR: AddressSanitizer: "
          r"(.*) on(?: unknown)? address 0x([0-9`a-f]+) (?:at |\()"
            r"pc 0x([0-9`a-f]+)"
            r" bp 0x([0-9`a-f]+)"
            r" sp 0x([0-9`a-f]+)"
            r"(?: T(\d+))?"
          r"\)?"
          r"\s*$",
          sLine,
          re.I,
        );
        if oSummaryMatch:
          assert int(oSummaryMatch.group(1)) == oProcess.uId, \
              "Expected process id %s, got %s" % (oProcess.uId, oSummaryMatch.group(1));
          break;
      else:
        continue; # Not found: try stderr of next process.
      break; # Found: stop.
    else:
      return; # Not found in any stderr: return.
    
    # Extract info from the summary
    (
      sThreadId, # Optional, unfortunately
      sASanBugType, sAddressHex,
      sIPHex,
      sBPHex,
      sSPHex,
      sThreadIndex, # "Tnnn" - not much use to us.
    ) = oSummaryMatch.groups();
    uThreadId = sThreadId and int(sThreadId) or None;
    uProblemAddress = int(sAddressHex, 16);
    
    # Check if the end of the ERROR message is in the output:
    sErrorMessageHeader = uThreadId and ("==%d:%d==" % (oProcess.uId, uThreadId)) or ("==%d==" % oProcess.uId);
    try:
      uEndIndex = asOutput.index(sErrorMessageHeader + "ABORTING", uStartIndex + 1) + 1;
    except ValueError:
      return; # No: return
    
    # Trim error message:
    asASanErrorMessage = asOutput[uStartIndex:uEndIndex];
    
    atxMemoryRemarks = [
      ("Address for which ASan reported this problem", uProblemAddress, None)
    ];
    
    uMemoryDumpStartAddress = None;
    uMemoryDumpEndAddress = None;
    sAction = None;
    for sLine in asASanErrorMessage[1:-1]:
      oAddressInfoMatch = re.match(
        r"^%s$" % "".join([
          r"0x([0-9a-f]+) is located (\d+) bytes (?:inside|to the (?:left|right)) of ",
          r"(",
            r"(\d+)\-byte region \[0x([0-9a-f]+),0x([0-9a-f]+)\)$",
          r"|",
            r"global variable '(.+)' defined in '.+' \(0x([0-9`a-f]+)\) of size (\d+)",
          r")",
        ]),
        sLine,
      );
      if oAddressInfoMatch:
        (
          sAddressHex,
          sOffset,
          sBlockSize, sBlockStartAddressHex, sBlockEndAddressHex,
          sVariableName, sVariableStartAddressHex, sVariableSize,
        ) = oAddressInfoMatch.groups();
        assert uProblemAddress == int(sAddressHex, 16), \
            "Problem reported at address 0x%X, but information provided for address 0x%s" % (uProblemAddress, sAddressHex);
        if sBlockSize:
          uBlockSize = int(sBlockSize);
          uBlockStartAddress = int(sBlockStartAddressHex, 16);
          uBlockEndAddress = int(sBlockEndAddressHex, 16);
          assert uBlockEndAddress - uBlockStartAddress == uBlockSize, \
              "The memory block start (0x%X) and end (0x%X) address suggest a size (0x%X) that do not agree with the reported size (0x%X)" % \
              (uBlockStartAddress, uBlockEndAddress, uBlockEndAddress - uBlockStartAddress, uBlockSize);
          if uMemoryDumpStartAddress is None or uBlockStartAddress < uMemoryDumpStartAddress:
            uMemoryDumpStartAddress = uBlockStartAddress;
          if uMemoryDumpEndAddress is None or uBlockEndAddress > uMemoryDumpEndAddress:
            uMemoryDumpEndAddress = uBlockEndAddress;
          atxMemoryRemarks.append(
            ("Memory block according to ASan", uBlockStartAddress, uBlockSize),
          );
        else:
          uVariableStartAddress = int(sVariableStartAddressHex, 16);
          uVariableSize = int(sVariableSize);
          if uMemoryDumpStartAddress is None or uVariableStartAddress < uMemoryDumpStartAddress:
            uMemoryDumpStartAddress = uVariableStartAddress;
          if uMemoryDumpEndAddress is None or uVariableStartAddress + uVariableSize > uMemoryDumpEndAddress:
            uMemoryDumpEndAddress = uVariableStartAddress + uVariableSize;
          atxMemoryRemarks.append(
            ("global variable %s" % sVariableName, uMemoryDumpStartAddress, uVariableSize),
          );
        continue;
      oActionInfoMatch = re.match(r"^(READ|WRITE) of size (\d+) at 0x([0-9a-f]+) thread T\d+", sLine);
      if oActionInfoMatch:
        sAction, sSize, sAddressHex = oActionInfoMatch.groups();
        uSize = int(sSize);
        uAddress = int(sAddressHex, 16);
        atxMemoryRemarks.append(
          ("Attempt to %s %d bytes from 0x%X" % (sAction.lower(), uSize, uAddress), uAddress, uSize),
        );
        continue;
      oActionMatch = re.match(r"^%sThe signal is caused by a (READ|WRITE) memory access\.$" % sErrorMessageHeader, sLine);
      if oActionMatch:
        (sAction,) = oActionMatch.groups();
        atxMemoryRemarks.append(
          ("Attempt to %s bytes from 0x%X" % (sAction.lower(), uProblemAddress), uProblemAddress, None),
        );
        continue;
      
    if sASanBugType == "access-violation":
      sViolationTypeId = {"READ": "R", "WRITE": "W"}.get(sAction, "?");
      uAccessViolationAddress = uProblemAddress;
      # TODO: Maybe call fbAccessViolation_HandleNULLPointer, etc. from the file
      # cBugReport_foAnalyzeException_STATUS_ACCESS_VIOLATION.py here?
      fUpdateReportForProcessThreadAccessViolationTypeIdAndAddress(
          oSelf.oCdbWrapper, oBugReport, oProcess, oThread, sViolationTypeId, uAccessViolationAddress);
      
    else:
      oBugReport.s0BugTypeId = "ASan:%s" % sASanBugType;
      oBugReport.s0SecurityImpact = dsSecurityImpact_by_sASanBugType.get(sASanBugType, "Unknown: this type of bug has not been analyzed before");
    oBugReport.s0BugDescription = "AddressSanitizer reported a %s on address 0x%X." % (sASanBugType, uProblemAddress);
    
    if oSelf.oCdbWrapper.bGenerateReportHTML:
      if uMemoryDumpStartAddress is None:
        # We know nothing about the layout of the memory region for which the problem was reported, but we do want to
        # dump it in the report, so we will output a region of a size that will hopefully be useful, but not too large
        # so as to bloat the report with irrelevant data.
        uMemoryDumpStartAddress = uProblemAddress - 0x100;
        uMemoryDumpSize = 0x200;
      else:
        # Make sure the problem address is in the memory dump
        if uMemoryDumpStartAddress > uProblemAddress:
          uMemoryDumpStartAddress = uProblemAddress;
        elif uMemoryDumpEndAddress < uProblemAddress:
          uMemoryDumpEndAddress = uProblemAddress;
        uMemoryDumpStartAddress, uMemoryDumpSize = ftuLimitedAndAlignedMemoryDumpStartAddressAndSize(
          uProblemAddress, oProcess.uPointerSize, uMemoryDumpStartAddress, uMemoryDumpEndAddress - uMemoryDumpStartAddress,
        );
      # Dump memory
      oBugReport.fAddMemoryDump(
        uStartAddress = uMemoryDumpStartAddress,
        uEndAddress = uMemoryDumpStartAddress + uMemoryDumpSize,
        s0AddressDescriptionHTML = None,
      );
      oBugReport.fAddMemoryRemarks(atxMemoryRemarks);
      # Add ASan output to file
      sASanOutputHTML = cBugReport.sBlockHTMLTemplate % {
        "sName": "ASan bug report",
        "sCollapsed": "Collapsed",
        "sContent": "<pre>%s</pre>" % "\r\n".join([
          fsCP437HTMLFromString(sLine, u0TabStop = 8) for sLine in asASanErrorMessage
        ])
      };
      oBugReport.asExceptionSpecificBlocksHTML.append(sASanOutputHTML);
