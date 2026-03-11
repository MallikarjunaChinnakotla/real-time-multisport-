import { useState, useEffect } from 'react';
import * as api from '../../../api';

const InputSelect = ({label, value, options, onChange}: {label: string, value: string, options: {id: string|number, label: string}[], onChange: (val: string)=>void}) => (
      <div className="mb-4 w-full">
          <label className="block text-xs text-gray-600 mb-1 font-medium select-none">{label}</label>
          <select 
             className="w-full bg-white border border-gray-200 text-gray-900 rounded px-3 py-2 outline-none focus:ring-1 focus:ring-blue-500 appearance-none"
             value={value} onChange={e => onChange(e.target.value)}
          >
             <option value="">Select...</option>
             {options.map(o => <option key={o.id} value={o.id}>{o.label}</option>)}
          </select>
      </div>
  );

export default function VolleyballScoring() {
  const sport = 'volleyball';
  const [tournaments, setTournaments] = useState<any[]>([]);
  const [matches, setMatches] = useState<any[]>([]);
  const [teams, setTeams] = useState<any[]>([]);
  const [players, setPlayers] = useState<any[]>([]);
  const [scores, setScores] = useState<any[]>([]);

  const [tid, setTid] = useState('');
  const [mid, setMid] = useState('');
  
  const [currentSet, setCurrentSet] = useState(1);
  const [pendingEvent, setPendingEvent] = useState<any>(null);
  const [selectedPlayer, setSelectedPlayer] = useState('');

  const fetchDat = async () => {
    const [tRes, mRes, tmRes, pRes] = await Promise.all([
      api.getTournaments(sport),
      api.getMatches(sport),
      api.getTeams(sport),
      api.getPlayers(sport)
    ]);
    setTournaments(tRes.data);
    setMatches(mRes.data);
    setTeams(tmRes.data);
    setPlayers(pRes.data);
  };

  const fetchScores = async (mId: number) => {
    const res = await api.getScores(sport, mId);
    setScores(res.data);
  };

  useEffect(() => { fetchDat(); }, []);
  useEffect(() => { if (mid) fetchScores(parseInt(mid)); }, [mid]);
  
  const activeMatch = matches.find(m => m.match_id == parseInt(mid));
  const tMatches = matches.filter(m => m.tournament_id == parseInt(tid));

  const getTeamName = (id: number) => teams.find(t => t.team_id == id)?.team_name || id;

  const team1Info = { id: activeMatch?.team1_id, name: getTeamName(activeMatch?.team1_id) };
  const team2Info = { id: activeMatch?.team2_id, name: getTeamName(activeMatch?.team2_id) };

  // Calculate points for the active set
  const getPointsForSet = (teamId: number, setNum: number) => {
      // we store 'set number' in the 'quarter' field
      return scores.filter(s => s.team_id == teamId && s.event_type === 'point' && (s.quarter == setNum || parseInt(s.quarter) == setNum)).length;
  };

  const t1CurrentSetPoints = getPointsForSet(team1Info.id, currentSet);
  const t2CurrentSetPoints = getPointsForSet(team2Info.id, currentSet);

  // Determine sets won locally
  let t1SetsWon = 0;
  let t2SetsWon = 0;
  
  // Checking Sets 1 to 5
  for(let i=1; i<=5; i++) {
     const t1P = getPointsForSet(team1Info.id, i);
     const t2P = getPointsForSet(team2Info.id, i);
     // simplified set win detection: 25 points, win by 2 (or 15 for 5th set)
     const target = i === 5 ? 15 : 25;
     if (t1P >= target && t1P - t2P >= 2) t1SetsWon++;
     else if (t2P >= target && t2P - t1P >= 2) t2SetsWon++;
  }

  const initiateEvent = (teamId: number, eventStr: string) => {
      setPendingEvent({ teamId, type: eventStr, label: eventStr.replace('_', ' ').toUpperCase() });
      setSelectedPlayer('');
  };

  const confirmEvent = async () => {
      if(!pendingEvent) return;
      if(!selectedPlayer) {
          alert("Please select a player who scored/performed the action.");
          return;
      }

      await api.addScore(sport, {
          match_id: parseInt(mid),
          minute: 1, 
          quarter: currentSet, // storing Set in quarter
          team_id: pendingEvent.teamId,
          player_id: selectedPlayer,
          event_type: `${pendingEvent.label} - ${players.find((p:any)=>p.player_id==selectedPlayer)?.player_name || 'Player'}`,
          points: pendingEvent.type === 'point' ? 1 : 0, 
          timestamp: new Date().toISOString()
      });
      setPendingEvent(null);
      fetchScores(parseInt(mid));
  };

  const endSet = () => {
      setCurrentSet(c => c + 1);
  };

  

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6 font-sans">
      <h1 className="text-3xl font-bold flex items-center gap-3">
          🏐 Live Volleyball Scoring
      </h1>

      <div className="mt-8">
          <InputSelect 
              label="Select Tournament" 
              value={tid} 
              onChange={val => {setTid(val); setMid('');}} 
              options={tournaments.map(t => ({id: t.tournament_id, label: t.tournament_name}))} 
          />

          <InputSelect 
              label="Select Match" 
              value={mid} 
              onChange={setMid} 
              options={tMatches.map(m => ({id: m.match_id, label: `Match #${m.match_id}: ${getTeamName(m.team1_id)} vs ${getTeamName(m.team2_id)}`}))} 
          />
      </div>

      {activeMatch && (
       <div className="mt-8 animate-fade-in border-t border-gray-300 pt-8">
          
          <div className="flex justify-between items-center bg-gray-100 p-6 rounded-lg border border-gray-200 mb-8">
             <div className="text-center w-1/3">
                 <h2 className="text-2xl font-bold text-gray-800 mb-2">{team1Info.name}</h2>
                 <p className="text-green-400 font-bold">Sets Won: {t1SetsWon}</p>
             </div>
             
             <div className="text-center w-1/3">
                 <div className="text-gray-600 text-sm font-bold uppercase tracking-widest mb-2">Set {currentSet}</div>
                 <div className="text-5xl font-black text-gray-900 bg-white px-6 py-4 rounded-xl border border-gray-200 shadow-inner inline-block">
                     {t1CurrentSetPoints} <span className="opacity-40 font-light mx-2">-</span> {t2CurrentSetPoints}
                 </div>
             </div>
             
             <div className="text-center w-1/3">
                 <h2 className="text-2xl font-bold text-gray-800 mb-2">{team2Info.name}</h2>
                 <p className="text-blue-400 font-bold">Sets Won: {t2SetsWon}</p>
             </div>
          </div>

          <div className="flex justify-center mb-10">
              <button onClick={endSet} className="bg-white hover:bg-gray-200 border border-gray-200 px-6 py-2 rounded text-blue-700 font-medium text-sm transition-colors shadow">
                  ⏩ Move to Set {currentSet + 1}
              </button>
          </div>

          {pendingEvent ? (
              <div className="bg-white border border-blue-200 rounded-lg p-6 mb-8 shadow-md text-center">
                  <h4 className="text-xl font-bold mb-4 text-blue-800">
                      Who scored/performed the {pendingEvent.label}?
                  </h4>
                  <div className="mb-4 text-left">
                      <InputSelect 
                          label="Select Player" 
                          value={selectedPlayer} 
                          onChange={setSelectedPlayer} 
                          options={players.filter((p:any) => p.team_id == pendingEvent.teamId).map((p:any) => ({id: p.player_id, label: p.player_name}))} 
                      />
                  </div>
                  <div className="flex gap-4 justify-center">
                      <button onClick={confirmEvent} className="bg-blue-600 hover:bg-blue-700 text-gray-900 font-bold py-2 px-6 rounded shadow">Confirm</button>
                      <button onClick={() => setPendingEvent(null)} className="bg-white hover:bg-gray-100 border border-gray-300 py-2 px-6 rounded font-semibold text-gray-700">Cancel</button>
                  </div>
              </div>
          ) : (
              <div className="grid grid-cols-2 gap-8">
                  <div className="bg-gray-50 p-5 rounded-lg border border-gray-200">
                      <h4 className="font-bold text-center mb-4 text-blue-700">{team1Info.name} Actions</h4>
                      <div className="space-y-3">
                          <button onClick={() => initiateEvent(team1Info.id, 'point')} className="w-full bg-green-50 border-l-4 border-green-500 hover:bg-green-100 text-green-800 py-4 rounded font-bold shadow-sm flex items-center justify-center gap-2 text-xl">+1 Point</button>
                          
                          <div className="grid grid-cols-2 gap-2 mt-4 pt-4 border-t border-gray-200">
                              <button onClick={() => initiateEvent(team1Info.id, 'spike')} className="bg-white hover:bg-gray-200 text-gray-800 py-2 rounded text-sm">Spike Kill</button>
                              <button onClick={() => initiateEvent(team1Info.id, 'block')} className="bg-white hover:bg-gray-200 text-gray-800 py-2 rounded text-sm">Block</button>
                              <button onClick={() => initiateEvent(team1Info.id, 'ace')} className="bg-white hover:bg-gray-200 text-gray-800 py-2 rounded text-sm col-span-2">Service Ace</button>
                          </div>
                      </div>
                  </div>

                  <div className="bg-gray-50 p-5 rounded-lg border border-gray-200">
                      <h4 className="font-bold text-center mb-4 text-blue-700">{team2Info.name} Actions</h4>
                      <div className="space-y-3">
                          <button onClick={() => initiateEvent(team2Info.id, 'point')} className="w-full bg-blue-50 border-l-4 border-blue-500 hover:bg-blue-100 text-blue-800 py-4 rounded font-bold shadow-sm flex items-center justify-center gap-2 text-xl">+1 Point</button>
                          
                          <div className="grid grid-cols-2 gap-2 mt-4 pt-4 border-t border-gray-200">
                              <button onClick={() => initiateEvent(team2Info.id, 'spike')} className="bg-white hover:bg-gray-200 text-gray-800 py-2 rounded text-sm">Spike Kill</button>
                              <button onClick={() => initiateEvent(team2Info.id, 'block')} className="bg-white hover:bg-gray-200 text-gray-800 py-2 rounded text-sm">Block</button>
                              <button onClick={() => initiateEvent(team2Info.id, 'ace')} className="bg-white hover:bg-gray-200 text-gray-800 py-2 rounded text-sm col-span-2">Service Ace</button>
                          </div>
                      </div>
                  </div>
              </div>
          )}
          
          {/* Match Log */}
          <div className="border-t border-gray-300 pt-6 mt-8">
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2 text-gray-900">📝 Play-by-Play (Set {currentSet})</h3>
              <ul className="space-y-2">
                  {[...scores]
                      .filter(s => parseInt(s.quarter) == currentSet)
                      .reverse().slice(0, 10).map((s, idx) => {
                      return (
                          <li key={idx} className="text-sm bg-gray-50 border border-gray-200 px-4 py-2 rounded flex items-center gap-3">
                              <span className="font-bold text-gray-600 capitalize">{s.event_type}</span>
                              <span className="text-gray-800 ml-2">by {getTeamName(s.team_id)}</span>
                              {s.event_type === 'point' && <span className="ml-auto text-green-400 font-bold">+1</span>}
                          </li>
                      );
                  })}
                  {scores.filter(s => parseInt(s.quarter) == currentSet).length === 0 && <li className="text-gray-500 italic text-sm">No points recorded in this set.</li>}
              </ul>
          </div>
       </div>
      )}
    </div>
  );
}
