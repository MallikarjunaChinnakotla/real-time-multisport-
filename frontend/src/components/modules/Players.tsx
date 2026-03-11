import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import * as api from '../../api';

const Players = () => {
  const { sport } = useParams<{ sport: string }>();
  const [teams, setTeams] = useState<any[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [players, setPlayers]  = useState<any[]>([]);
  
  const [name, setName] = useState('');
  const [tid, setTid] = useState('');
  const [phone, setPhone] = useState('');

  const fetchP = async () => {
    if (!sport) return;
    const [tRes, pRes] = await Promise.all([
        api.getTeams(sport),
        api.getPlayers(sport)
    ]);
    setTeams(tRes.data);
    setPlayers(pRes.data);
  };

  useEffect(() => { fetchP(); }, [sport]);

  const add = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sport) return;
    if (!name || !tid) {
      alert("Please provide a player name and select a team.");
      return;
    }
    try {
      await api.addPlayer(sport, { player_name: name, team_id: parseInt(tid), phone_number: phone, profile_image: '' });
      fetchP();
      setName(''); setPhone('');
    } catch (error) {
      console.error("Error adding player:", error);
      alert("Failed to add player. Please try again.");
    }
  };

  const del = async (id: number) => {
    if (!sport) return;
    await api.deletePlayer(sport, id);
    fetchP();
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">Add Player</h3>
        <form onSubmit={add} className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <select className="border rounded p-2 outline-none" value={tid} onChange={e => setTid(e.target.value)}>
             <option value="">Select Team</option>
             {teams.map(t => <option key={t.team_id} value={t.team_id}>{t.team_name}</option>)}
          </select>
          <input className="border rounded p-2 focus:ring-2 focus:ring-blue-500 outline-none" placeholder="Player Name" value={name} onChange={e => setName(e.target.value)} />
          <input className="border rounded p-2 focus:ring-2 focus:ring-blue-500 outline-none" placeholder="Phone Number" value={phone} onChange={e => setPhone(e.target.value)} />
          <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded shadow transition-colors">Add Player</button>
        </form>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">View Players</h3>
        
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
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Team ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Phone</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {players.filter(item => JSON.stringify(item).toLowerCase().includes(searchTerm.toLowerCase())).map(p => (
                <tr key={p.player_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{p.player_id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{p.player_name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{p.team_id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{p.phone_number}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button onClick={() => del(p.player_id)} className="text-red-600 hover:text-red-900">Delete</button>
                  </td>
                </tr>
              ))}
              {players.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center text-sm text-gray-500">No players found</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
export default Players;
