"use client";

import { Activity, BarChart3, Bell, Home, MapPin, Menu, Settings, Sun, X, Zap } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

/**
 * Mobile Navigation Component
 * Responsive hamburger menu for mobile devices.
 * Part of v1.1.0 Mobile-Responsive Dashboard (PWA) feature.
 */

interface NavItem {
  href: string;
  label: string;
  labelTh: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  {
    href: "/",
    label: "Dashboard",
    labelTh: "แดชบอร์ด",
    icon: <Home className="h-5 w-5" />,
  },
  {
    href: "/forecast/solar",
    label: "Solar Forecast",
    labelTh: "พยากรณ์พลังงานแสงอาทิตย์",
    icon: <Sun className="h-5 w-5" />,
  },
  {
    href: "/forecast/voltage",
    label: "Voltage Monitor",
    labelTh: "ตรวจสอบแรงดัน",
    icon: <Zap className="h-5 w-5" />,
  },
  {
    href: "/alerts",
    label: "Alerts",
    labelTh: "การแจ้งเตือน",
    icon: <Bell className="h-5 w-5" />,
  },
  {
    href: "/analysis",
    label: "Analysis",
    labelTh: "วิเคราะห์",
    icon: <BarChart3 className="h-5 w-5" />,
  },
  {
    href: "/network",
    label: "Network",
    labelTh: "โครงข่าย",
    icon: <Activity className="h-5 w-5" />,
  },
  {
    href: "/regions",
    label: "Regions",
    labelTh: "ภูมิภาค",
    icon: <MapPin className="h-5 w-5" />,
  },
  {
    href: "/settings",
    label: "Settings",
    labelTh: "ตั้งค่า",
    icon: <Settings className="h-5 w-5" />,
  },
];

export function MobileNavigation() {
  const [isOpen, setIsOpen] = useState(false);
  const pathname = usePathname();

  // Close menu on route change
  useEffect(() => {
    setIsOpen(false);
  }, []);

  // Prevent body scroll when menu is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  return (
    <>
      {/* Mobile Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200 lg:hidden">
        <div className="flex items-center justify-between h-14 px-4">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-violet-600 to-indigo-600 rounded-lg flex items-center justify-center">
              <Sun className="h-5 w-5 text-white" />
            </div>
            <span className="font-semibold text-gray-900">PEA Forecast</span>
          </Link>

          <button
            type="button"
            onClick={() => setIsOpen(!isOpen)}
            className="p-2 -mr-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label={isOpen ? "Close menu" : "Open menu"}
            aria-expanded={isOpen}
          >
            {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>
      </header>

      {/* Mobile Menu Overlay */}
      <div
        className={cn(
          "fixed inset-0 z-40 bg-black/50 transition-opacity lg:hidden",
          isOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        )}
        onClick={() => setIsOpen(false)}
        aria-hidden="true"
      />

      {/* Mobile Menu Panel */}
      <nav
        className={cn(
          "fixed top-14 left-0 bottom-0 z-40 w-72 bg-white shadow-xl transition-transform duration-300 ease-in-out lg:hidden",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
        aria-label="Mobile navigation"
      >
        <div className="flex flex-col h-full overflow-y-auto">
          <div className="flex-1 py-4">
            <ul className="space-y-1 px-3">
              {navItems.map((item) => {
                const isActive =
                  pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));

                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={cn(
                        "flex items-center gap-3 px-3 py-3 rounded-lg transition-colors",
                        isActive
                          ? "bg-violet-50 text-violet-700"
                          : "text-gray-700 hover:bg-gray-100"
                      )}
                    >
                      <span className={cn(isActive ? "text-violet-600" : "text-gray-500")}>
                        {item.icon}
                      </span>
                      <div className="flex flex-col">
                        <span className="font-medium">{item.label}</span>
                        <span className="text-xs text-gray-500">{item.labelTh}</span>
                      </div>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>

          {/* Menu Footer */}
          <div className="border-t border-gray-200 p-4">
            <div className="text-xs text-gray-500 text-center">
              <p>PEA RE Forecast Platform</p>
              <p>แพลตฟอร์มพยากรณ์พลังงานหมุนเวียน</p>
              <p className="mt-1">v1.1.0</p>
            </div>
          </div>
        </div>
      </nav>

      {/* Spacer for fixed header */}
      <div className="h-14 lg:hidden" />
    </>
  );
}

/**
 * Bottom Navigation Bar for Mobile
 * Quick access to main sections from bottom of screen.
 */
export function BottomNavigation() {
  const pathname = usePathname();

  const bottomNavItems = navItems.slice(0, 5); // First 5 items

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-gray-200 lg:hidden safe-area-bottom">
      <ul className="flex items-center justify-around h-16">
        {bottomNavItems.map((item) => {
          const isActive =
            pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));

          return (
            <li key={item.href}>
              <Link
                href={item.href}
                className={cn(
                  "flex flex-col items-center justify-center w-16 h-full transition-colors",
                  isActive ? "text-violet-600" : "text-gray-500 hover:text-gray-700"
                )}
              >
                {item.icon}
                <span className="text-[10px] mt-1 font-medium truncate max-w-[60px]">
                  {item.label}
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
