import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  HomeIcon,
  BuildingOfficeIcon,
  CpuChipIcon,
  Cog6ToothIcon,
  ChartBarSquareIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '../auth/AuthProvider';

interface LayoutProps {
  children: React.ReactNode;
}

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Brands', href: '/brands', icon: BuildingOfficeIcon },
  { name: 'Agents', href: '/agents', icon: CpuChipIcon },
  { name: 'Observability', href: '/observability', icon: ChartBarSquareIcon },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
];

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const { logout, user } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg">
        <div className="flex h-16 items-center justify-center border-b border-gray-200 px-6">
          <Link to="/dashboard" className="flex items-center justify-center" aria-label="NOVA dashboard">
            <img src="/brand/nova-logo.svg" alt="NOVA" className="h-9 w-auto" />
          </Link>
        </div>
        
        <nav className="mt-8 px-3">
          <div className="space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <div key={item.name}>
                  <Link
                    to={item.href}
                    className={`
                      group flex gap-x-3 rounded-md px-3 py-2 text-sm font-semibold leading-6
                      ${isActive
                        ? 'bg-primary-50 text-primary-600'
                        : 'text-gray-700 hover:bg-gray-50 hover:text-primary-600'
                      }
                    `}
                  >
                    <item.icon
                      className={`h-6 w-6 shrink-0 ${
                        isActive ? 'text-primary-600' : 'text-gray-400 group-hover:text-primary-600'
                      }`}
                      aria-hidden="true"
                    />
                    {item.name}
                  </Link>
                </div>
              );
            })}
          </div>
        </nav>
      </div>

      {/* Main content */}
      <div className="pl-64">
        <div className="border-b border-gray-200 bg-white">
          <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
            <div>
              <p className="text-sm font-semibold text-gray-900">Operator session</p>
              <p className="text-xs text-gray-500">
                Signed in as {user?.full_name || user?.email || 'Dashboard user'}.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                className="rounded-md bg-gray-900 px-3 py-2 text-sm font-semibold text-white hover:bg-gray-800"
                onClick={() => void logout()}
                type="button"
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
        <main className="min-h-[calc(100vh-73px)] py-8">
          <div className="mx-auto flex min-h-[calc(100vh-137px)] max-w-7xl flex-col px-4 sm:px-6 lg:px-8">
            <div className="flex-1">
              {children}
            </div>
            <footer className="mt-10 border-t border-gray-200 py-6 text-xs text-gray-500">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <span className="font-semibold text-gray-700">NOVA</span> is built by Fractics.
                  {' '}© {new Date().getFullYear()} Fractics. All rights reserved.
                </div>
                <a
                  className="font-medium text-gray-600 hover:text-primary-600"
                  href="https://fractics.com"
                  rel="noreferrer"
                  target="_blank"
                >
                  fractics.com
                </a>
              </div>
            </footer>
          </div>
        </main>
      </div>
    </div>
  );
}
