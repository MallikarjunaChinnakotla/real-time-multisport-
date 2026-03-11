import React, { useState, useEffect } from 'react';
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

export default function TableTennisScoring() {
  const sport = 'table_tennis';
  const [tournaments, setTournaments] = useState<any[]>([]);
  const [matches, setMatches] = useState<any[]>([]);
  const [teams, setTeams] = useState<any[]>([]);
  const [scores, setScores] = useState<any[]>([]);

  const [tid, setTid] = useState('');
  const [mid, setMid] = useState('');
  
  const [currentGame, setCurrentGame] = useState(1);

  const fetchDat = async () => {
    const [tRes, mRes, tmRes] = await Promise.all([
      api.getTournaments(sport),
      api.getMatches(sport),
      api.getTeams(sport)
    ]);
    setTournaments(tRes.data);
    setMatches(mRes.data);
    setTeams(tmRes.data);
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

  // Calculate points for the active game
  const getPointsForGame = (teamId: number, gameNum: number) => {
      // we store 'game number' in the 'quarter' field
      return scores.filter(s => s.team_id == teamId && s.event_type === 'point' && (s.quarter == gameNum || parseInt(s.quarter) == gameNum)).length;
  };

  const t1CurrentGamePoints = getPointsForGame(team1Info.id, currentGame);
  const t2CurrentGamePoints = getPointsForGame(team2Info.id, currentGame);

  // Determine games won locally
  let t1GamesWon = 0;
  let t2GamesWon = 0;
  
  // Checking Games 1 to 7
  for(let i=1; i<=7; i++) {
     const t1P = getPointsForGame(team1Info.id, i);
     const t2P = getPointsForGame(team2Info.id, i);
     // standard win condition: 11 points, win by 2
     if (t1P >= 11 && t1P - t2P >= 2) t1GamesWon++;
     else if (t2P >= 11 && t2P - t1P >= 2) t2GamesWon++;
  }

  const recordEvent = async (teamId: number, eventStr: string = 'point') => {
      await api.addScore(sport, {
          match_id: parseInt(mid),
          minute: 1, 
          quarter: currentGame, // storing Game in quarter
          team_id: teamId,
          player_id: '',
          event_type: eventStr,
          points: eventStr === 'point' ? 1 : 0, 
          timestamp: new Date().toISOString()
      });
      fetchScores(parseInt(mid));
  };

  const endGame = () => {
      setCurrentGame(c => c + 1);
  };

  

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6 font-sans">
      <h1 className="text-3xl font-bold flex items-center gap-3">
          🏓 Live Table Tennis Scoring
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
                 <p className="text-green-400 font-bold">Games Won: {t1GamesWon}</p>
             </div>
             
             <div className="text-center w-1/3">
                 <div className="text-gray-600 text-sm font-bold uppercase tracking-widest mb-2">Game {currentGame}</div>
                 <div className="text-5xl font-black text-gray-900 bg-white px-6 py-4 rounded-xl border border-gray-200 shadow-inner inline-block">
                     {t1CurrentGamePoints} <span className="opacity-40 font-light mx-2">-</span> {t2CurrentGamePoints}
                 </div>
             </div>
             
             <div className="text-center w-1/3">
                 <h2 className="text-2xl font-bold text-gray-800 mb-2">{team2Info.name}</h2>
                 <p className="text-blue-400 font-bold">Games Won: {t2GamesWon}</p>
             </div>
          </div>

          <div className="flex justify-center mb-10">
              <button onClick={endGame} className="bg-white hover:bg-gray-200 border border-gray-200 px-6 py-2 rounded text-blue-700 font-medium text-sm transition-colors shadow">
                  ⏩ Move to Game {currentGame + 1}
              </button>
          </div>

          <div className="grid grid-cols-2 gap-8">
              <div className="bg-gray-50 p-5 rounded-lg border border-gray-200">
                  <h4 className="font-bold text-center mb-4 text-blue-700">{team1Info.name} Actions</h4>
                  <div className="space-y-3">
                      <button onClick={() => recordEvent(team1Info.id, 'point')} className="w-full bg-green-50 border-l-4 border-green-500 hover:bg-green-100 text-green-800 py-4 rounded font-bold shadow-sm flex items-center justify-center gap-2 text-xl">+1 Point</button>
                  </div>
              </div>

              <div className="bg-gray-50 p-5 rounded-lg border border-gray-200">
                  <h4 className="font-bold text-center mb-4 text-blue-700">{team2Info.name} Actions</h4>
                  <div className="space-y-3">
                      <button onClick={() => recordEvent(team2Info.id, 'point')} className="w-full bg-blue-50 border-l-4 border-blue-500 hover:bg-blue-100 text-blue-800 py-4 rounded font-bold shadow-sm flex items-center justify-center gap-2 text-xl">+1 Point</button>
                  </div>
              </div>
          </div>
          
          {/* Match Log */}
          <div className="border-t border-gray-300 pt-6 mt-8">
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2 text-gray-900">📝 Play-by-Play (Game {currentGame})</h3>
              <ul className="space-y-2">
                  {[...scores]
                      .filter(s => parseInt(s.quarter) == currentGame)
                      .reverse().slice(0, 5).map((s, idx) => {
                      return (
                          <li key={idx} className="text-sm bg-gray-50 border border-gray-200 px-4 py-2 rounded flex items-center gap-3">
                              <span className="font-bold text-gray-600 capitalize">{s.event_type}</span>
                              <span className="text-gray-800 ml-2">by {getTeamName(s.team_id)}</span>
                              {s.event_type === 'point' && <span className="ml-auto text-green-400 font-bold">+1</span>}
                          </li>
                      );
                  })}
                  {scores.filter(s => parseInt(s.quarter) == currentGame).length === 0 && <li className="text-gray-500 italic text-sm">No points recorded in this game.</li>}
              </ul>
          </div>
       </div>
      )}
    </div>
  );
}
