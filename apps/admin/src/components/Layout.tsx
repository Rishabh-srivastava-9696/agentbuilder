import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  HomeIcon,
  BuildingOfficeIcon,
  CpuChipIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';
import { clearAdminApiKey, getAdminApiKey, setAdminApiKey } from '../api/client';

interface LayoutProps {
  children: React.ReactNode;
}

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Brands', href: '/brands', icon: BuildingOfficeIcon },
  { name: 'Agents', href: '/agents', icon: CpuChipIcon },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
];

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const [adminApiKey, setAdminApiKeyInput] = useState(() => getAdminApiKey());

  const handleSaveAdminKey = () => {
    setAdminApiKey(adminApiKey);
    setAdminApiKeyInput(getAdminApiKey());
  };

  const handleClearAdminKey = () => {
    clearAdminApiKey();
    setAdminApiKeyInput('');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg">
        <div className="flex h-16 items-center justify-center border-b border-gray-200">
          <h1 className="text-xl font-bold text-gray-900">Agent Builder</h1>
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
              <p className="text-sm font-semibold text-gray-900">Admin write access</p>
              <p className="text-xs text-gray-500">
                Enter the admin key for this browser session only. It is no longer shipped in runtime config.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <input
                aria-label="Admin API key"
                className="w-72 rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                onChange={(event) => setAdminApiKeyInput(event.target.value)}
                placeholder="Paste admin API key"
                type="password"
                value={adminApiKey}
              />
              <button
                className="rounded-md bg-gray-900 px-3 py-2 text-sm font-semibold text-white hover:bg-gray-800"
                onClick={handleSaveAdminKey}
                type="button"
              >
                Save
              </button>
              <button
                className="rounded-md border border-gray-300 px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50"
                onClick={handleClearAdminKey}
                type="button"
              >
                Clear
              </button>
            </div>
          </div>
        </div>
        <main className="py-8">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
