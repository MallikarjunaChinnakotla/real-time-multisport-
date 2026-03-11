import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import * as api from '../../api';

const Tournaments = () => {
  const { sport } = useParams<{ sport: string }>();
  const [tournaments, setTournaments]  = useState<any[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [name, setName] = useState('');
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const [location, setLocation] = useState('');

  const fetchT = async () => {
    if (!sport) return;
    try {
      const res = await api.getTournaments(sport);
      setTournaments(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchT();
  }, [sport]);

  const add = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sport) return;
    if (!name || !start || !end || !location) {
      alert("Please fill in all tournament details.");
      return;
    }
    try {
      await api.addTournament(sport, {
        tournament_name: name,
        start_date: start,
        end_date: end,
        location: location
      });
      fetchT();
      setName(''); setStart(''); setEnd(''); setLocation('');
    } catch (e) {
      console.error(e);
    }
  };

  const del = async (id: number) => {
    if (!sport) return;
    await api.deleteTournament(sport, id);
    fetchT();
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">Add Tournament</h3>
        <form onSubmit={add} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <input className="border rounded p-2 focus:ring-2 focus:ring-blue-500 outline-none" placeholder="Tournament Name" value={name} onChange={e => setName(e.target.value)} />
          <input className="border rounded p-2" type="date" placeholder="Start Date" value={start} onChange={e => setStart(e.target.value)} />
          <input className="border rounded p-2" type="date" placeholder="End Date" value={end} onChange={e => setEnd(e.target.value)} />
          <input className="border rounded p-2 focus:ring-2 focus:ring-blue-500 outline-none" placeholder="Location" value={location} onChange={e => setLocation(e.target.value)} />
          <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded shadow transition-colors">Add</button>
        </form>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">View Tournaments</h3>
        
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
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Start</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">End</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Location</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {tournaments.filter(item => JSON.stringify(item).toLowerCase().includes(searchTerm.toLowerCase())).map(t => (
                <tr key={t.tournament_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{t.tournament_id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{t.tournament_name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{t.start_date}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{t.end_date}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{t.location}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button onClick={() => del(t.tournament_id)} className="text-red-600 hover:text-red-900">Delete</button>
                  </td>
                </tr>
              ))}
              {tournaments.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-4 text-center text-sm text-gray-500">No tournaments found</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
export default Tournaments;
