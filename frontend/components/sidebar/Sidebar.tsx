"use client";

/**
 * Re-export of ``NavigationSidebar`` under the legacy ``Sidebar`` name.
 *
 * The original inline sidebar component was replaced by the dedicated
 * ``NavigationSidebar`` component.  This file preserves the import path
 * used by ``app/page.tsx`` and ``components/chat/ChatWindow.tsx``.
 */
export { NavigationSidebar as Sidebar } from "./NavigationSidebar";
