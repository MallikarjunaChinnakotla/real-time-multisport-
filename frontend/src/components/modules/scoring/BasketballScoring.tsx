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

export default function BasketballScoring() {
  const sport = 'basketball';
  const [tournaments, setTournaments] = useState<any[]>([]);
  const [matches, setMatches] = useState<any[]>([]);
  const [teams, setTeams] = useState<any[]>([]);
  const [players, setPlayers] = useState<any[]>([]);
  const [scores, setScores] = useState<any[]>([]);

  const [tid, setTid] = useState('');
  const [mid, setMid] = useState('');
  
  const [pendingEvent, setPendingEvent] = useState<any>(null);
  const [selectedPlayer, setSelectedPlayer] = useState('');
  
  const [timer, setTimer] = useState(600); // 10 minutes
  const [isRunning, setIsRunning] = useState(false);

  // Coin Toss State
  const [tossCompleted, setTossCompleted] = useState(false);
  const [tossWinner, setTossWinner] = useState('');
  const [tossDecision, setTossDecision] = useState('');
  const [tossResult, setTossResult] = useState('');
  const [isTossing, setIsTossing] = useState(false);

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
    if(res.data && res.data.length > 0) {
        setTossCompleted(true);
    } else {
        setTossCompleted(false);
    }
  };

  useEffect(() => { fetchDat(); }, []);
  useEffect(() => { if (mid) fetchScores(parseInt(mid)); }, [mid]);
  
  useEffect(() => {
    let interval: any;
    if (isRunning && timer > 0) {
      interval = setInterval(() => setTimer(t => t - 1), 1000);
    }
    return () => clearInterval(interval);
  }, [isRunning, timer]);

  const activeMatch = matches.find(m => m.match_id == parseInt(mid));
  const tMatches = matches.filter(m => m.tournament_id == parseInt(tid));

  const getTeamName = (id: number) => teams.find(t => t.team_id == id)?.team_name || id;

  const team1Info = { id: activeMatch?.team1_id, name: getTeamName(activeMatch?.team1_id) };
  const team2Info = { id: activeMatch?.team2_id, name: getTeamName(activeMatch?.team2_id) };
  
  const team1Score = scores.filter(s => s.team_id == team1Info.id).reduce((sum, s) => sum + (parseInt(s.points) || 0), 0);
  const team2Score = scores.filter(s => s.team_id == team2Info.id).reduce((sum, s) => sum + (parseInt(s.points) || 0), 0);

  // Compute Quarter Breakdowns
  const getQuarterPoints = (teamId: number, q: number) => {
      return scores.filter(s => s.team_id == teamId && parseInt(s.quarter || s.period || s.minute || "1") === q).reduce((sum, s) => sum + (parseInt(s.points) || 0), 0);
  };

  const formatTimer = (secs: number) => {
      const m = Math.floor(secs / 60).toString().padStart(2, '0');
      const s = (secs % 60).toString().padStart(2, '0');
      return `${m}:${s}`;
  };

  const initiateEvent = (teamId: number, points: number, type: string) => {
      setPendingEvent({ teamId, points, type, label: type.replace('_', ' ').toUpperCase() });
      setSelectedPlayer('');
  };

  const confirmEvent = async () => {
      if(!pendingEvent) return;
      if(!selectedPlayer && pendingEvent.type !== 'timeout') {
          alert("Please select a player who scored/performed the action.");
          return;
      }

      await api.addScore(sport, {
          match_id: parseInt(mid),
          minute: Math.floor((600 - timer) / 60) + 1,
          quarter: 1, // Defaulting to Q1, normally dynamic based on timer
          team_id: pendingEvent.teamId,
          player_id: selectedPlayer,
          points: pendingEvent.points,
          event_type: pendingEvent.type === 'timeout' ? pendingEvent.type : `${pendingEvent.label} - ${players.find((p:any)=>p.player_id==selectedPlayer)?.player_name || 'Player'}`,
          timestamp: new Date().toISOString()
      });
      setPendingEvent(null);
      fetchScores(parseInt(mid));
  };

  const handleTossSubmit = () => {
      if(tossWinner && tossDecision) {
          setTossCompleted(true);
      } else {
          alert('Please select winner and decision');
      }
  };

  const handleFlipCoin = () => {
      if (!activeMatch || isTossing) return;
      setIsTossing(true);
      setTossResult('');
      setTossWinner('');
      
      setTimeout(() => {
          const isHeads = Math.random() > 0.5;
          setTossResult(isHeads ? 'Heads' : 'Tails');
          
          const team1Wins = Math.random() > 0.5;
          setTossWinner(team1Wins ? activeMatch.team1_id.toString() : activeMatch.team2_id.toString());
          
          setIsTossing(false);
      }, 1000);
  };

  

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6 font-sans">
      <h1 className="text-3xl font-bold flex items-center gap-3">
          🏀 badsketball Dashboard
      </h1>
      <p className="text-gray-600 text-sm mb-4">Live basketball stats go here...</p>

      <h2 className="text-xl font-bold mt-8">🏀 Update Live Score</h2>

      <div className="mt-4">
          <InputSelect 
              label="Select Tournament" 
              value={tid} 
              onChange={val => {setTid(val); setMid('');}} 
              options={tournaments.map(t => ({id: t.tournament_id, label: t.tournament_name}))} 
          />

          <InputSelect 
              label="Select Match" 
              value={mid} 
              onChange={val => {setMid(val); setTossCompleted(false);}} 
              options={tMatches.map(m => ({id: m.match_id, label: `Match #${m.match_id}: ${getTeamName(m.team1_id)} vs ${getTeamName(m.team2_id)}`}))} 
          />
      </div>

      {activeMatch && !tossCompleted && (
          <div className="mt-8 bg-gray-50 border border-gray-200 p-8 rounded-xl shadow-sm text-center animate-fade-in">
              <h2 className="text-2xl font-bold mb-6 text-gray-800">🪙 Coin Toss</h2>
              <div className="flex flex-col items-center justify-center mb-6">
                  <div 
                      onClick={handleFlipCoin}
                      className={`w-28 h-28 bg-yellow-400 rounded-full border-[6px] border-yellow-600 flex items-center justify-center text-yellow-800 font-black text-2xl shadow-xl hover:scale-105 cursor-pointer ${isTossing ? 'animate-spin cursor-not-allowed' : 'transition-transform'}`}
                  >
                      {isTossing ? '...' : (tossResult ? tossResult : 'FLIP')}
                  </div>
                  {tossResult && !isTossing && (
                      <div className="mt-4 text-green-700 font-bold text-lg animate-fade-in">It's {tossResult}!</div>
                  )}
              </div>
              <div className="flex justify-center gap-8 mb-6">
                  <div>
                      <h4 className="font-semibold mb-2 text-gray-700">Toss Winner</h4>
                      <select className="bg-white border text-gray-800 px-4 py-2 rounded shadow-sm" value={tossWinner} onChange={e => setTossWinner(e.target.value)}>
                          <option value="">-- Select --</option>
                          <option value={activeMatch.team1_id}>{getTeamName(activeMatch.team1_id)}</option>
                          <option value={activeMatch.team2_id}>{getTeamName(activeMatch.team2_id)}</option>
                      </select>
                  </div>
                  {tossWinner && (
                      <div className="animate-fade-in">
                          <h4 className="font-semibold mb-2 text-gray-700">Decision</h4>
                          <select className="bg-white border text-gray-800 px-4 py-2 rounded shadow-sm" value={tossDecision} onChange={e => setTossDecision(e.target.value)}>
                              <option value="">-- Select --</option>
                              <option value="Side A">Side A</option>
                              <option value="Side B">Side B</option>
                          </select>
                      </div>
                  )}
              </div>
              {tossDecision && (
                  <button onClick={handleTossSubmit} className="bg-blue-600 hover:bg-blue-700 text-gray-900 font-bold py-2 px-8 rounded shadow">Start Match</button>
              )}
          </div>
      )}

      {activeMatch && tossCompleted && (
       <div className="mt-8 animate-fade-in border-t border-gray-300 pt-8">
          <h2 className="text-xl font-bold flex items-center gap-2 mb-6">⏱️ Match Timer</h2>
          
          <div className="flex gap-4 mb-6">
              <button onClick={() => setIsRunning(true)} className="bg-white border border-gray-200 px-4 py-2 rounded font-medium hover:bg-gray-200 transition-colors text-gray-900 text-sm flex items-center">
                  ▶️ Start/Resume
              </button>
              <button onClick={() => setIsRunning(false)} className="bg-white border border-gray-200 px-4 py-2 rounded font-medium hover:bg-gray-200 transition-colors text-gray-900 text-sm flex items-center">
                  ⏸️ Pause
              </button>
              <button onClick={() => {setIsRunning(false); setTimer(600);}} className="bg-white border border-gray-200 px-4 py-2 rounded font-medium hover:bg-red-50 transition-colors text-gray-900 text-sm flex items-center">
                  🔄 Reset
              </button>
          </div>
          
          <h2 className="text-3xl font-bold mb-8 font-mono">{formatTimer(timer)} <span className="text-gray-500 text-lg font-sans">(Countdown)</span></h2>

          <div className="text-center py-8">
            <h1 className="text-4xl font-black text-[#55C370]">{team1Info.name} {team1Score} - {team2Score} {team2Info.name}</h1>
          </div>

          <h3 className="text-xl font-bold mt-8 mb-4">Quarter Breakdown</h3>
          <div className="bg-gray-100 border border-gray-200 rounded-lg overflow-hidden mb-8">
             <table className="w-full text-left text-sm text-gray-800">
                <thead className="bg-gray-200">
                    <tr>
                        <th className="px-4 py-3 border-b border-gray-200 w-[20%]"></th>
                        <th className="px-4 py-3 border-b border-gray-200">Q1</th>
                        <th className="px-4 py-3 border-b border-gray-200">Q2</th>
                        <th className="px-4 py-3 border-b border-gray-200">Q3</th>
                        <th className="px-4 py-3 border-b border-gray-200">Q4</th>
                    </tr>
                </thead>
                <tbody>
                    <tr className="border-b border-gray-200">
                        <td className="px-4 py-3 font-medium bg-gray-50 border-r border-gray-200">{team1Info.name}</td>
                        <td className="px-4 py-3 border-r border-gray-200">{getQuarterPoints(team1Info.id, 1)}</td>
                        <td className="px-4 py-3 border-r border-gray-200">{getQuarterPoints(team1Info.id, 2)}</td>
                        <td className="px-4 py-3 border-r border-gray-200">{getQuarterPoints(team1Info.id, 3)}</td>
                        <td className="px-4 py-3">{getQuarterPoints(team1Info.id, 4)}</td>
                    </tr>
                    <tr>
                        <td className="px-4 py-3 font-medium bg-gray-50 border-r border-gray-200">{team2Info.name}</td>
                        <td className="px-4 py-3 border-r border-gray-200">{getQuarterPoints(team2Info.id, 1)}</td>
                        <td className="px-4 py-3 border-r border-gray-200">{getQuarterPoints(team2Info.id, 2)}</td>
                        <td className="px-4 py-3 border-r border-gray-200">{getQuarterPoints(team2Info.id, 3)}</td>
                        <td className="px-4 py-3">{getQuarterPoints(team2Info.id, 4)}</td>
                    </tr>
                </tbody>
             </table>
          </div>

          <button className="bg-white border border-gray-200 px-4 py-2 rounded text-red-700 font-semibold hover:bg-red-50 transition-colors mb-6 text-sm flex items-center">
             ❌ Reset Form
          </button>

          {pendingEvent ? (
              <div className="bg-white border border-blue-200 rounded-lg p-6 mb-8 shadow-md text-center">
                  <h4 className="text-xl font-bold mb-4 text-blue-800">
                      Who scored/performed the {pendingEvent.label}?
                  </h4>
                  {pendingEvent.type !== 'timeout' && (
                      <div className="mb-4 text-left">
                          <InputSelect 
                              label="Select Player" 
                              value={selectedPlayer} 
                              onChange={setSelectedPlayer} 
                              options={players.filter((p:any) => p.team_id == pendingEvent.teamId).map((p:any) => ({id: p.player_id, label: p.player_name}))} 
                          />
                      </div>
                  )}
                  <div className="flex gap-4 justify-center">
                      <button onClick={confirmEvent} className="bg-blue-600 hover:bg-blue-700 text-gray-900 font-bold py-2 px-6 rounded shadow">Confirm</button>
                      <button onClick={() => setPendingEvent(null)} className="bg-white hover:bg-gray-100 border border-gray-300 py-2 px-6 rounded font-semibold text-gray-700">Cancel</button>
                  </div>
              </div>
          ) : (
              <>
                  <h3 className="text-xl font-bold mt-4 mb-4">Select Score / Event</h3>
                  <div className="grid grid-cols-3 gap-3">
                      <button onClick={() => initiateEvent(team1Info.id, 1, 'free_throw')} className="bg-white border border-gray-200 px-4 py-3 rounded text-sm hover:bg-gray-200 transition-colors flex justify-center items-center gap-2">🏀 {team1Info.name} 1 PT</button>
                      <button onClick={() => initiateEvent(team1Info.id, 2, 'field_goal')} className="bg-white border border-gray-200 px-4 py-3 rounded text-sm hover:bg-gray-200 transition-colors flex justify-center items-center gap-2">🏀 {team1Info.name} 2 PT</button>
                      <button onClick={() => initiateEvent(team1Info.id, 3, 'three_pointer')} className="bg-white border border-gray-200 px-4 py-3 rounded text-sm hover:bg-gray-200 transition-colors flex justify-center items-center gap-2">🏀 {team1Info.name} 3 PT</button>

                      <button onClick={() => initiateEvent(team2Info.id, 1, 'free_throw')} className="bg-white border border-gray-200 px-4 py-3 rounded text-sm hover:bg-gray-200 transition-colors flex justify-center items-center gap-2">🏀 {team2Info.name} 1 PT</button>
                      <button onClick={() => initiateEvent(team2Info.id, 2, 'field_goal')} className="bg-white border border-gray-200 px-4 py-3 rounded text-sm hover:bg-gray-200 transition-colors flex justify-center items-center gap-2">🏀 {team2Info.name} 2 PT</button>
                      <button onClick={() => initiateEvent(team2Info.id, 3, 'three_pointer')} className="bg-white border border-gray-200 px-4 py-3 rounded text-sm hover:bg-gray-200 transition-colors flex justify-center items-center gap-2">🏀 {team2Info.name} 3 PT</button>
                  </div>
                  <div className="grid grid-cols-4 gap-3 mt-3">
                      <button onClick={() => initiateEvent(team1Info.id, 0, 'foul')} className="bg-white border border-gray-200 px-4 py-3 rounded text-sm text-red-700 hover:bg-red-50 transition-colors flex justify-center items-center gap-2">🚫 {team1Info.name} Foul</button>
                      <button onClick={() => initiateEvent(team2Info.id, 0, 'foul')} className="bg-white border border-gray-200 px-4 py-3 rounded text-sm text-red-700 hover:bg-red-50 transition-colors flex justify-center items-center gap-2">🚫 {team2Info.name} Foul</button>
                      <button onClick={() => initiateEvent(team1Info.id, 0, 'timeout')} className="bg-white border border-gray-200 px-4 py-3 rounded text-sm text-blue-700 hover:bg-gray-100 transition-colors flex justify-center items-center gap-2">⏱ {team1Info.name} TO</button>
                      <button onClick={() => initiateEvent(team2Info.id, 0, 'timeout')} className="bg-white border border-gray-200 px-4 py-3 rounded text-sm text-blue-700 hover:bg-gray-100 transition-colors flex justify-center items-center gap-2">⏱ {team2Info.name} TO</button>
                  </div>
              </>
          )}

       </div>
      )}
    </div>
  );
}
