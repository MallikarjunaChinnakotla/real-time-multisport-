import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { Menu, Home } from 'lucide-react';

const SPORTS = [
  "cricket", "football", "basketball", "volleyball", 
  "kabaddi", "handball", "table_tennis", "hockey", "softball"
];

const Layout: React.FC = () => {
  return (
    <div className="flex h-screen bg-gray-50 text-gray-900">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r flex flex-col">
        <div className="h-16 flex items-center px-4 border-b font-bold text-xl text-blue-600">
          <Menu className="mr-2 h-6 w-6" /> Multi-Sports
        </div>
        <nav className="flex-1 overflow-y-auto p-4 space-y-1">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `flex items-center px-3 py-2 rounded-md transition-colors ${
                isActive ? 'bg-blue-50 text-blue-700 font-medium' : 'hover:bg-gray-100'
              }`
            }
          >
            <Home className="mr-3 h-5 w-5" /> Home
          </NavLink>
          <div className="pt-4 pb-2 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">
            Sports Dashboard
          </div>
          {SPORTS.map((sport) => (
            <NavLink
              key={sport}
              to={`/${sport}`}
              className={({ isActive }) =>
                `flex items-center px-3 py-2 rounded-md capitalize transition-colors ${
                  isActive ? 'bg-blue-50 text-blue-700 font-medium' : 'hover:bg-gray-100'
                }`
              }
            >
              {sport.replace('_', ' ')}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 bg-white border-b flex items-center px-8 shadow-sm justify-between">
          <h1 className="text-xl font-semibold capitalize bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">Dashboard</h1>
        </header>
        <div className="flex-1 overflow-auto p-8 bg-gray-50">
          <div className="max-w-7xl mx-auto bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden min-h-[calc(100vh-8rem)] flex flex-col">
            <Outlet />
          </div>
        </div>
      </main>
    </div>
  );
};

export default Layout;
