import re;
from cBugReport import cBugReport;
from ftuLimitedAndAlignedMemoryDumpStartAddressAndSize import ftuLimitedAndAlignedMemoryDumpStartAddressAndSize;
from sBlockHTMLTemplate import sBlockHTMLTemplate;

dsSecurityImpact_by_sASanBugType = {
  "use-after-poison": "Potentially exploitable security issue",
  "global-buffer-overflow": "Potentially exploitable security issue",
  "heap-use-after-free": "Potentially exploitable security issue",
};

def foDetectAndCreateBugReportForASan(oCdbWrapper, uExceptionCode):
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
  asAsanBugReport = [];
  uMemoryDumpStartAddress = None;
  uMemoryDumpEndAddress = None;
  atxMemoryRemarks = [];
  for sLine in oCdbWrapper.asStdErrOutput:
    if not asAsanBugReport:
      oSummaryMatch = re.match(r"^==(\d+):(\d+)==ERROR: AddressSanitizer: (.*) on address 0x([0-9`a-f]+) at pc 0x([0-9`a-f]+) bp 0x([0-9`a-f]+) sp 0x([0-9`a-f]+)$", sLine, re.I);
      if not oSummaryMatch:
        continue;
      sProcessId, sThreadId, sASanBugType, sAddressHex, sIPHex, sBPHex, sSPHex = oSummaryMatch.groups();
      uProcessId = long(sProcessId);
      uThreadId = long(sThreadId);
      uProblemAddress = long(sAddressHex, 16);
      atxMemoryRemarks.append(("Address for which ASan reported this problem", uProblemAddress, None));
    elif sLine == "==%d:%d==ABORTING" % (uProcessId, uThreadId):
      break;
    else:
      oHeapInfoMatch = re.match(r"0x([0-9`a-f]+) is located (\d+) bytes (?:inside|to the (?:left|right)) of (\d+)\-byte region \[0x([0-9`a-f]+),0x([0-9`a-f]+)\)", sLine, re.I);
      if oHeapInfoMatch:
        sAddressHex, sOffset, sBlockSize, sBlockStartAddressHex, sBlockEndAddressHex = oHeapInfoMatch.groups();
        assert uProblemAddress == long(sAddressHex, 16), \
            "Problem reported at address 0x%X, but information provided for address 0x%s" % (uProblemAddress, sAddressHex);
        uBlockStartAddress = long(sBlockStartAddressHex, 16);
        uBlockEndAddress = long(sBlockEndAddressHex, 16);
        uBlockSize = long(sBlockSize);
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
      oHeapInfoMatch = re.match(r"0x([0-9`a-f]+) is located (\d+) bytes (?:inside|to the (?:left|right)) of global variable '(.+)' defined in '.+' \(0x([0-9`a-f]+)\) of size (\d+)", sLine, re.I);
      if oHeapInfoMatch:
        sAddressHex, sOffset, sVariableName, sVariableStartAddressHex, sVariableSize = oHeapInfoMatch.groups();
        assert uProblemAddress == long(sAddressHex, 16), \
            "Problem reported at address 0x%X, but information provided for address 0x%s" % (uProblemAddress, sAddressHex);
        uVariableStartAddress = long(sVariableStartAddressHex, 16);
        uVariableSize = long(sVariableSize);
        if uMemoryDumpStartAddress is None or uVariableStartAddress < uMemoryDumpStartAddress:
          uMemoryDumpStartAddress = uVariableStartAddress;
        if uMemoryDumpEndAddress is None or uVariableStartAddress + uVariableSize > uMemoryDumpEndAddress:
          uMemoryDumpEndAddress = uVariableStartAddress + uVariableSize;
        atxMemoryRemarks.append(
          ("global variable %s" % sVariableName, uMemoryDumpStartAddress, uVariableSize),
        );
      oHeapInfoMatch = re.match(r"(READ|WRITE) of size (\d+) at 0x([0-9`a-f]+) thread T\d+", sLine, re.I);
      if oHeapInfoMatch:
        sAction, sSize, sAddressHex = oHeapInfoMatch.groups();
        uSize = long(sSize);
        uAddress = long(sAddressHex, 16);
        atxMemoryRemarks.append(
          ("Attempt to %s %d bytes from 0x%X" % (sAction.lower(), uSize, uAddress), uAddress, uSize),
        );
    asAsanBugReport.append(sLine);
  else:
    if asAsanBugReport:
      # We found the start of a bug report, but not the end. It may be the application was interrupted while ASan was
      # busy collecting and outputting information. We will ignore this exception, as there should be another one when
      # ASan is finished, at which point all relevant information is available for us in  our report.
      return;
    # We did not find a bug report.
    return;
  oCdbWrapper.fSelectProcess(uProcessId);
  oProcess = oCdbWrapper.oCurrentProcess;
  sBugTypeId = "ASan:%s" % sASanBugType;
  sBugDescription = "AddressSanitizer reported a %s on address 0x%X." % (sASanBugType, uProblemAddress);
  sSecurityImpact = dsSecurityImpact_by_sASanBugType.get(sASanBugType, "Unknown: this type of bug has not been analyzed before");
  oHeapManagerData = oProcess.foGetHeapManagerDataForAddress(uProblemAddress);
  if oHeapManagerData:
    atxMemoryRemarks.extend(oHeapManagerData.fatxMemoryRemarks());
    # Make sure entire page heap block is included in the memory dump.
    if oHeapManagerData.uMemoryDumpStartAddress < uMemoryDumpStartAddress:
      uMemoryDumpStartAddress = oHeapManagerData.uMemoryDumpStartAddress;
      assert uMemoryDumpEndAddress - uMemoryDumpStartAddress == uMemoryDumpSize, \
          "Something, somewhere went wrong because 0x%X - 0x%X == 0x%X and not 0x%X" % \
          (uMemoryDumpEndAddress, uMemoryDumpStartAddress, uMemoryDumpEndAddress - uMemoryDumpStartAddress, uMemoryDumpSize);
    if oHeapManagerData.uMemoryDumpEndAddress > uMemoryDumpEndAddress:
      uMemoryDumpEndAddress = ooHeapManagerData.uMemoryDumpEndAddress;
  
  oBugReport = cBugReport.foCreate(oProcess, sBugTypeId, sBugDescription, sSecurityImpact);
  if oCdbWrapper.bGenerateReportHTML:
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
      uMemoryDumpStartAddress,
      uMemoryDumpStartAddress + uMemoryDumpSize,
      "Memory near heap block at 0x%X" % uMemoryDumpStartAddress,
    );
    for (sDescription, uAddress, uSize) in atxMemoryRemarks:
      print "$$$ 0x%08X+%s %s" % (uAddress, uSize is None and "????" or "%04X" % uSize, sDescription);
    oBugReport.atxMemoryRemarks.extend(atxMemoryRemarks);
    # Add ASan output to file
    sASanOutputHTML = sBlockHTMLTemplate % {
      "sName": "ASan bug report",
      "sCollapsed": "Collapsed",
      "sContent": "<pre>%s</pre>" % "\r\n".join([
        oCdbWrapper.fsHTMLEncode(s, uTabStop = 8) for s in asAsanBugReport
      ])
    };
    oBugReport.asExceptionSpecificBlocksHTML.append(sASanOutputHTML);
  return oBugReport;