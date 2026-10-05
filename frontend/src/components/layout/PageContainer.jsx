import React, { useState } from 'react';
import Navbar from './Navbar';
import Sidebar from './Sidebar';

/**
 * PageContainer Layout Wrapper
 * Assembles sticky Navbar, responsive/mobile collapsible Sidebar, and main scrollable content area.
 */
export default function PageContainer({ children, fullWidth = false }) {
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-925 text-slate-900 dark:text-slate-100 flex flex-col transition-colors duration-200">
      {/* Sticky Header Navbar */}
      <Navbar
        isSidebarOpen={isMobileSidebarOpen}
        onToggleSidebar={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)}
      />

      {/* Main Layout Area: Sidebar + Scrollable View */}
      <div className="flex-1 flex max-w-7xl w-full mx-auto">
        <Sidebar isOpen={isMobileSidebarOpen} onClose={() => setIsMobileSidebarOpen(false)} />

        <main
          className={`flex-1 min-w-0 py-6 px-4 sm:px-6 lg:px-8 ${
            fullWidth ? 'max-w-full' : 'max-w-5xl'
          } mx-auto w-full`}
        >
          {children}
        </main>
      </div>
    </div>
  );
}
