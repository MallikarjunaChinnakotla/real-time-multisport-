import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import * as api from '../../api';

const Schedule = () => {
  const { sport } = useParams<{ sport: string }>();
  const [tournaments, setTournaments] = useState<any[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [teams, setTeams] = useState<any[]>([]);
  const [matches, setMatches]  = useState<any[]>([]);
  
  const [tid, setTid] = useState('');
  const [team1, setTeam1] = useState('');
  const [team2, setTeam2] = useState('');
  const [date, setDate] = useState('');
  const [venue, setVenue] = useState('');
  const [overs, setOvers] = useState('20');

  const fetchDat = async () => {
    if (!sport) return;
    const [tRes, tmRes, mRes] = await Promise.all([
        api.getTournaments(sport),
        api.getTeams(sport),
        api.getMatches(sport)
    ]);
    setTournaments(tRes.data);
    setTeams(tmRes.data);
    setMatches(mRes.data);
  };

  useEffect(() => { fetchDat(); }, [sport]);

  const add = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sport) return;
    if (!tid || !team1 || !team2 || !date || !venue) {
      alert("Please fill out all match details.");
      return;
    }
    if (team1 === team2) return alert("Select different teams");
    
    const payload: any = {
        tournament_id: parseInt(tid),
        team1_id: parseInt(team1),
        team2_id: parseInt(team2),
        match_date: date,
        venue: venue
    };
    if (sport === 'cricket') payload.overs_per_innings = parseInt(overs);
    
    try {
      await api.addMatch(sport, payload);
      fetchDat();
      setTeam1(''); setTeam2(''); setDate(''); setVenue('');
    } catch (error) {
      console.error("Error scheduling match", error);
      alert("Failed to schedule match. Please try again.");
    }
  };

  const del = async (id: number) => {
    if (!sport) return;
    await api.deleteMatch(sport, id);
    fetchDat();
  };

  const getTeamName = (id: number) => teams.find(t => t.team_id === id)?.team_name || id;

  const tTeams = teams.filter(t => t.tournament_id === parseInt(tid));

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">Schedule Match</h3>
        <form onSubmit={add} className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <select className="border rounded p-2 outline-none" value={tid} onChange={e => setTid(e.target.value)}>
             <option value="">Select Tournament</option>
             {tournaments.map(t => <option key={t.tournament_id} value={t.tournament_id}>{t.tournament_name}</option>)}
          </select>
          <select className="border rounded p-2 outline-none" value={team1} onChange={e => setTeam1(e.target.value)}>
             <option value="">Team 1</option>
             {tTeams.map(t => <option key={t.team_id} value={t.team_id}>{t.team_name}</option>)}
          </select>
          <select className="border rounded p-2 outline-none" value={team2} onChange={e => setTeam2(e.target.value)}>
             <option value="">Team 2</option>
             {tTeams.map(t => <option key={t.team_id} value={t.team_id}>{t.team_name}</option>)}
          </select>
          <input className="border rounded p-2" type="date" value={date} onChange={e => setDate(e.target.value)} />
          <input className="border rounded p-2 focus:ring-2 focus:ring-blue-500 outline-none" placeholder="Venue" value={venue} onChange={e => setVenue(e.target.value)} />
          {sport === 'cricket' && (
              <input className="border rounded p-2" type="number" placeholder="Overs per Innings" value={overs} onChange={e => setOvers(e.target.value)} />
          )}
          <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded shadow transition-colors md:col-span-full">Schedule Match</button>
        </form>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">Scheduled Matches</h3>
        
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
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Match ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tournament</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Team 1 vs Team 2</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date / Venue</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {matches.filter(item => JSON.stringify(item).toLowerCase().includes(searchTerm.toLowerCase())).map(m => (
                <tr key={m.match_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{m.match_id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{m.tournament_id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{getTeamName(m.team1_id)} vs {getTeamName(m.team2_id)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{m.match_date} at {m.venue}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button onClick={() => del(m.match_id)} className="text-red-600 hover:text-red-900">Delete</button>
                  </td>
                </tr>
              ))}
              {matches.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center text-sm text-gray-500">No matches found</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
export default Schedule;
