import React from 'react';
import { Routes, Route, NavLink, useParams, Navigate } from 'react-router-dom';
import Tournaments from './modules/Tournaments';
import Teams from './modules/Teams';
import Players from './modules/Players';
import Schedule from './modules/Schedule';
import LiveScoring from './modules/LiveScoring';
import Stats from './modules/Stats';
import Awards from './modules/Awards';
import classNames from 'classnames';
import { Trophy, Users, UserPlus, Calendar, Activity, BarChart2, Star } from 'lucide-react';

const MODULES = [
  { path: 'tournaments', label: 'Tournaments', icon: Trophy },
  { path: 'teams', label: 'Teams', icon: Users },
  { path: 'players', label: 'Players', icon: UserPlus },
  { path: 'schedule', label: 'Schedule Match', icon: Calendar },
  { path: 'live-scoring', label: 'Live Scoring', icon: Activity },
  { path: 'stats', label: 'Statistics', icon: BarChart2 },
  { path: 'awards', label: 'Awards & Summary', icon: Star },
];

const SportDashboard: React.FC = () => {
  const { sport } = useParams<{ sport: string }>();

  return (
    <div className="flex flex-col h-full bg-white flex-1">
      <div className="px-6 py-4 bg-gray-50/50 border-b flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-800 capitalize flex items-center">
          <span className="bg-blue-100 text-blue-800 p-2 rounded-lg mr-3 shadow-inner">
            <Trophy className="h-6 w-6" />
          </span>
          {sport?.replace('_', ' ')} Dashboard
        </h2>
      </div>

      <div className="flex border-b overflow-x-auto bg-white px-2">
        {MODULES.map((m) => {
          const Icon = m.icon;
          return (
            <NavLink
              key={m.path}
              to={`/${sport}/${m.path}`}
              className={({ isActive }) =>
                classNames(
                  'px-5 py-4 whitespace-nowrap font-medium text-sm flex items-center transition-all border-b-2',
                  isActive
                    ? 'border-blue-600 text-blue-700 bg-blue-50/50'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 hover:bg-gray-50'
                )
              }
            >
              <Icon className="mr-2 h-4 w-4" />
              {m.label}
            </NavLink>
          )
        })}
      </div>

      <div className="flex-1 overflow-auto bg-gray-50/20 p-6">
        <Routes>
          <Route path="/" element={<Navigate to="tournaments" replace />} />
          <Route path="tournaments" element={<Tournaments />} />
          <Route path="teams" element={<Teams />} />
          <Route path="players" element={<Players />} />
          <Route path="schedule" element={<Schedule />} />
          <Route path="live-scoring" element={<LiveScoring />} />
          <Route path="stats" element={<Stats />} />
          <Route path="awards" element={<Awards />} />
        </Routes>
      </div>
    </div>
  );
};

export default SportDashboard;
