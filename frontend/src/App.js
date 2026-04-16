import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard, ListVideo, Zap, History, BookTemplate, BarChart2,
  Settings, ChevronLeft, ChevronRight, Youtube, Menu, X, Plus
} from 'lucide-react';
import { Sheet, SheetContent, SheetTrigger } from './components/ui/sheet';
import { Button } from './components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './components/ui/tooltip';
import { Toaster } from './components/ui/sonner';
import { Separator } from './components/ui/separator';
import Dashboard from './pages/Dashboard';
import Queue from './pages/Queue';
import Pipeline from './pages/Pipeline';
import HistoryPage from './pages/HistoryPage';
import Templates from './pages/Templates';
import Analytics from './pages/Analytics';
import SettingsPage from './pages/SettingsPage';
import './App.css';

const NAV_ITEMS = [
  { label: 'Dashboard', path: '/', icon: LayoutDashboard, group: 'overview' },
  { label: 'Queue', path: '/queue', icon: ListVideo, group: 'automation' },
  { label: 'Pipeline', path: '/pipeline', icon: Zap, group: 'automation' },
  { label: 'History', path: '/history', icon: History, group: 'automation' },
  { label: 'Templates', path: '/templates', icon: BookTemplate, group: 'library' },
  { label: 'Analytics', path: '/analytics', icon: BarChart2, group: 'insights' },
  { label: 'Settings', path: '/settings', icon: Settings, group: 'admin' },
];

const GROUP_LABELS = {
  overview: 'Overview',
  automation: 'Automation',
  library: 'Library',
  insights: 'Insights',
  admin: 'Admin'
};

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

function SidebarNav({ collapsed }) {
  const location = useLocation();
  let lastGroup = null;

  return (
    <nav className="flex flex-col gap-0.5 px-2">
      {NAV_ITEMS.map((item) => {
        const Icon = item.icon;
        const isActive = location.pathname === item.path ||
          (item.path !== '/' && location.pathname.startsWith(item.path));
        const showGroupHeader = !collapsed && item.group !== lastGroup;
        if (showGroupHeader) lastGroup = item.group;

        return (
          <React.Fragment key={item.path}>
            {showGroupHeader && (
              <p className="text-[10px] font-semibold tracking-widest uppercase text-muted-foreground px-2 pt-4 pb-1">
                {GROUP_LABELS[item.group]}
              </p>
            )}
            <TooltipProvider delayDuration={0}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <NavLink
                    to={item.path}
                    data-testid={`sidebar-nav-${item.label.toLowerCase()}-link`}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors duration-150 ${
                      isActive
                        ? 'bg-white/5 border border-white/10 text-foreground nav-item-active'
                        : 'text-muted-foreground hover:bg-white/3 hover:text-foreground'
                    }`}
                  >
                    <Icon size={18} className={isActive ? 'text-primary' : ''} />
                    {!collapsed && <span className="font-medium">{item.label}</span>}
                  </NavLink>
                </TooltipTrigger>
                {collapsed && (
                  <TooltipContent side="right">{item.label}</TooltipContent>
                )}
              </Tooltip>
            </TooltipProvider>
          </React.Fragment>
        );
      })}
    </nav>
  );
}

function AppLayout({ children }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-background dark">
      {/* Desktop Sidebar */}
      <aside
        className={`hidden lg:flex flex-col border-r border-border bg-card transition-all duration-200 ${
          collapsed ? 'w-[72px]' : 'w-[220px]'
        } shrink-0`}
      >
        {/* Logo */}
        <div className={`flex items-center gap-2 px-4 py-4 border-b border-border ${
          collapsed ? 'justify-center' : ''
        }`}>
          <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center shrink-0">
            <Youtube size={18} className="text-white" />
          </div>
          {!collapsed && (
            <div>
              <p className="text-sm font-semibold text-foreground leading-tight">Redline</p>
              <p className="text-[10px] text-muted-foreground">Studio</p>
            </div>
          )}
        </div>

        {/* Navigation */}
        <div className="flex-1 overflow-y-auto py-2">
          <SidebarNav collapsed={collapsed} />
        </div>

        {/* Collapse Toggle */}
        <div className="border-t border-border p-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setCollapsed(!collapsed)}
            className="w-full justify-center"
            data-testid="sidebar-collapse-button"
          >
            {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </Button>
        </div>
      </aside>

      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-4 py-3 bg-card border-b border-border">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-md bg-primary flex items-center justify-center">
            <Youtube size={14} className="text-white" />
          </div>
          <span className="text-sm font-semibold">Redline Studio</span>
        </div>
        <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
          <SheetTrigger asChild>
            <Button variant="ghost" size="sm">
              <Menu size={20} />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-64 bg-card border-border p-0">
            <div className="flex items-center gap-2 px-4 py-4 border-b border-border">
              <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
                <Youtube size={18} className="text-white" />
              </div>
              <div>
                <p className="text-sm font-semibold">Redline Studio</p>
                <p className="text-[10px] text-muted-foreground">YouTube Automation</p>
              </div>
            </div>
            <div className="py-2" onClick={() => setMobileOpen(false)}>
              <SidebarNav collapsed={false} />
            </div>
          </SheetContent>
        </Sheet>
      </div>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden flex flex-col min-h-screen">
        <div className="flex-1 overflow-y-auto pt-0 lg:pt-0 mt-[52px] lg:mt-0">
          <AnimatePresence mode="wait">
            <motion.div
              key={window.location.pathname}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.18 }}
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>

      <Toaster position="top-right" theme="dark" />
    </div>
  );
}

function App() {
  return (
    <div className="App dark">
      <BrowserRouter>
        <AppLayout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/queue" element={<Queue />} />
            <Route path="/pipeline" element={<Pipeline />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/templates" element={<Templates />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </AppLayout>
      </BrowserRouter>
    </div>
  );
}

export default App;
