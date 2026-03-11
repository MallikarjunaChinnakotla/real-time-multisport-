import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import * as api from '../../api';

const Teams = () => {
  const { sport } = useParams<{ sport: string }>();
  const [tournaments, setTournaments] = useState<any[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [teams, setTeams]  = useState<any[]>([]);
  
  const [name, setName] = useState('');
  const [tid, setTid] = useState('');

  const fetchT = async () => {
    if (!sport) return;
    const [tRes, teamsRes] = await Promise.all([
        api.getTournaments(sport),
        api.getTeams(sport)
    ]);
    setTournaments(tRes.data);
    setTeams(teamsRes.data);
  };

  useEffect(() => { fetchT(); }, [sport]);

  const add = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sport) return;
    if (!name || !tid) {
      alert("Please provide a team name and select a tournament.");
      return;
    }
    try {
      await api.addTeam(sport, { team_name: name, tournament_id: parseInt(tid) });
      fetchT();
      setName('');
    } catch (error) {
      console.error("Error adding team:", error);
      alert("Failed to add team. Please try again.");
    }
  };

  const del = async (id: number) => {
    if (!sport) return;
    await api.deleteTeam(sport, id);
    fetchT();
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">Add Team</h3>
        <form onSubmit={add} className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <select className="border rounded p-2 outline-none" value={tid} onChange={e => setTid(e.target.value)}>
             <option value="">Select Tournament</option>
             {tournaments.map(t => <option key={t.tournament_id} value={t.tournament_id}>{t.tournament_name}</option>)}
          </select>
          <input className="border rounded p-2 focus:ring-2 focus:ring-blue-500 outline-none" placeholder="Team Name" value={name} onChange={e => setName(e.target.value)} />
          <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded shadow transition-colors">Add Team</button>
        </form>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">View Teams</h3>
        
        <div className="mb-4">
          <input 
            type="text" 
            placeholder="Search..." 
            className="w-full border border-gray-300 rounded-lg p-2 focus:ring-2 focus:ring-blue-500 outline-none"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Team ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Team Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tournament ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {teams.filter(item => JSON.stringify(item).toLowerCase().includes(searchTerm.toLowerCase())).map(t => (
                <tr key={t.team_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{t.team_id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{t.team_name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{t.tournament_id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button onClick={() => del(t.team_id)} className="text-red-600 hover:text-red-900">Delete</button>
                  </td>
                </tr>
              ))}
              {teams.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-6 py-4 text-center text-sm text-gray-500">No teams found</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
export default Teams;
