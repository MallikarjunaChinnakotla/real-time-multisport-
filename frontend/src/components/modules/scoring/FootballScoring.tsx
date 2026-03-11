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

export default function FootballScoring() {
  const sport = 'football';
  const [tournaments, setTournaments] = useState<any[]>([]);
  const [matches, setMatches] = useState<any[]>([]);
  const [teams, setTeams] = useState<any[]>([]);
  const [players, setPlayers] = useState<any[]>([]);
  const [scores, setScores] = useState<any[]>([]);

  const [tid, setTid] = useState('');
  const [mid, setMid] = useState('');
  
  const [timer, setTimer] = useState(0); // counts up in seconds
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
    if (isRunning) {
      interval = setInterval(() => setTimer(t => t + 1), 1000);
    }
    return () => clearInterval(interval);
  }, [isRunning]);

  const activeMatch = matches.find(m => m.match_id == parseInt(mid));
  const tMatches = matches.filter(m => m.tournament_id == parseInt(tid));

  const getTeamName = (id: number) => teams.find(t => t.team_id == id)?.team_name || id;

  const team1Info = { id: activeMatch?.team1_id, name: getTeamName(activeMatch?.team1_id) };
  const team2Info = { id: activeMatch?.team2_id, name: getTeamName(activeMatch?.team2_id) };
  
  const formatTimer = (secs: number) => {
      const m = Math.floor(secs / 60).toString().padStart(2, '0');
      const s = (secs % 60).toString().padStart(2, '0');
      return `${m}:${s}`;
  };
  
  const currentMinute = Math.floor(timer / 60) + 1;

  // Calculate Goals
  // In football, event_type="goal" gives 1 point to the team. 
  // event_type="own_goal" gives 1 point to the OPPONENT.
  const t1Goals = scores.filter(s => 
      (s.team_id == team1Info.id && s.event_type === 'goal') || 
      (s.team_id == team2Info.id && s.event_type === 'own_goal')
  ).length;
  
  const t2Goals = scores.filter(s => 
      (s.team_id == team2Info.id && s.event_type === 'goal') || 
      (s.team_id == team1Info.id && s.event_type === 'own_goal')
  ).length;

  const [pendingEvent, setPendingEvent] = useState<{teamId: number, type: string, label: string} | null>(null);
  const [selectedPlayer1, setSelectedPlayer1] = useState('');
  const [selectedPlayer2, setSelectedPlayer2] = useState('');

  const initiateEvent = (teamId: number, type: string, label: string) => {
      setPendingEvent({ teamId, type, label });
      setSelectedPlayer1('');
      setSelectedPlayer2('');
  };

  const confirmEvent = async () => {
      if(!pendingEvent) return;
      
      let finalEventStr = pendingEvent.type;
      let finalPlayerId = selectedPlayer1;
      
      if (pendingEvent.type === 'substitution') {
          if (!selectedPlayer1 || !selectedPlayer2) {
              alert('Please select both Player Out and Player In.');
              return;
          }
          finalEventStr = `Substitution | Out: ${players.find(p=>p.player_id==selectedPlayer1)?.player_name} In: ${players.find(p=>p.player_id==selectedPlayer2)?.player_name}`;
          finalPlayerId = `${selectedPlayer1},${selectedPlayer2}`;
      } else {
          if (!selectedPlayer1 && pendingEvent.type !== 'own_goal') {
              alert('Please select a player.');
              return;
          }
          // if it's not sub, we can embed the player name into the log natively if we want, or rely on player_id
      }

      await api.addScore(sport, {
          match_id: parseInt(mid),
          minute: currentMinute,
          team_id: pendingEvent.teamId,
          player_id: finalPlayerId,
          event_type: finalEventStr, // 'goal', 'own_goal', 'yellow_card', 'red_card', 'substitution', etc
          points: finalEventStr.includes('goal') ? 1 : 0, 
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
          ⚽ Live Football Scoring
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
                              <option value="Kick-off">Kick-off</option>
                              <option value="Side">Side</option>
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
          
          <div className="flex justify-between items-center mb-6">
             <h2 className="text-xl font-bold flex items-center gap-2">⏱️ Match Clock</h2>
             <div className="flex gap-2">
                 <button onClick={() => setIsRunning(true)} className="bg-blue-50 border border-blue-200 text-blue-700 px-4 py-2 rounded text-sm font-medium hover:bg-blue-100">
                     ▶️ Start
                 </button>
                 <button onClick={() => setIsRunning(false)} className="bg-orange-50 border border-orange-200 text-[#E5C7A2] px-4 py-2 rounded text-sm font-medium hover:bg-orange-100">
                     ⏸️ Pause
                 </button>
             </div>
          </div>
          
          <div className="text-center mb-10">
              <h2 className="text-5xl font-mono font-bold text-gray-900 mb-2">{formatTimer(timer)}</h2>
              <p className="text-gray-600 font-medium">Minute: {currentMinute}'</p>
          </div>

          <div className="grid grid-cols-3 items-center text-center py-8 bg-gray-100 border border-gray-200 rounded-xl mb-10 shadow-lg relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-green-500 to-blue-500"></div>
              
              <div>
                  <h3 className="text-2xl font-bold text-gray-800 mb-2">{team1Info.name}</h3>
              </div>
              
              <div className="flex justify-center items-center gap-4">
                  <span className="text-6xl font-black text-gray-900">{t1Goals}</span>
                  <span className="text-3xl font-bold text-gray-500">-</span>
                  <span className="text-6xl font-black text-gray-900">{t2Goals}</span>
              </div>
              
              <div>
                  <h3 className="text-2xl font-bold text-gray-800 mb-2">{team2Info.name}</h3>
              </div>
          </div>

          <h3 className="text-xl font-bold mt-4 mb-4">Record Events</h3>
          
          {pendingEvent ? (
              <div className="bg-white border border-blue-200 rounded-lg p-6 mb-8 shadow-md">
                  <h4 className="text-xl font-bold mb-4 text-blue-800">
                      {pendingEvent.label} - {getTeamName(pendingEvent.teamId)}
                  </h4>
                  {pendingEvent.type === 'substitution' ? (
                      <div className="grid grid-cols-2 gap-4 mb-4">
                          <InputSelect 
                              label="🔴 Player Out" 
                              value={selectedPlayer1} 
                              onChange={setSelectedPlayer1} 
                              options={players.filter(p => p.team_id == pendingEvent.teamId).map(p => ({id: p.player_id, label: p.player_name}))} 
                          />
                          <InputSelect 
                              label="🟢 Player In" 
                              value={selectedPlayer2} 
                              onChange={setSelectedPlayer2} 
                              options={players.filter(p => p.team_id == pendingEvent.teamId).map(p => ({id: p.player_id, label: p.player_name}))} 
                          />
                      </div>
                  ) : pendingEvent.type === 'own_goal' ? (
                      <div className="mb-4">
                          <InputSelect 
                              label="🤷 Who scored the Own Goal?" 
                              value={selectedPlayer1} 
                              onChange={setSelectedPlayer1} 
                              options={players.filter(p => p.team_id == pendingEvent.teamId).map(p => ({id: p.player_id, label: p.player_name}))} 
                          />
                      </div>
                  ) : (
                      <div className="mb-4">
                          <InputSelect 
                              label="Select Player" 
                              value={selectedPlayer1} 
                              onChange={setSelectedPlayer1} 
                              options={players.filter(p => p.team_id == pendingEvent.teamId).map(p => ({id: p.player_id, label: p.player_name}))} 
                          />
                      </div>
                  )}
                  <div className="flex gap-4">
                      <button onClick={confirmEvent} className="bg-blue-600 hover:bg-blue-700 text-gray-900 font-bold py-2 px-6 rounded shadow">Confirm</button>
                      <button onClick={() => setPendingEvent(null)} className="bg-white hover:bg-gray-100 border border-gray-300 py-2 px-6 rounded font-semibold text-gray-700">Cancel</button>
                  </div>
              </div>
          ) : (
              <div className="grid grid-cols-2 gap-8">
                  {/* Team 1 Controls */}
                  <div className="bg-gray-50 p-5 rounded-lg border border-gray-200">
                      <h4 className="font-bold text-center mb-4 text-blue-700">{team1Info.name}</h4>
                      <div className="space-y-3">
                          <button onClick={() => initiateEvent(team1Info.id, 'goal', '⚽ Goal')} className="w-full bg-green-50 border-l-4 border-green-500 hover:bg-green-100 text-green-800 py-3 rounded font-bold shadow-sm flex items-center justify-center gap-2">⚽ Goal</button>
                          <button onClick={() => initiateEvent(team1Info.id, 'own_goal', '🤦‍♂️ Own Goal')} className="w-full bg-red-50 hover:bg-red-100 text-red-700 py-2 rounded font-medium text-sm flex items-center justify-center gap-2">🤦‍♂️ Own Goal (Score to {team2Info.name})</button>
                          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-gray-200">
                              <button onClick={() => initiateEvent(team1Info.id, 'yellow_card', '🟨 Yellow Card')} className="bg-yellow-50 hover:bg-yellow-100 text-yellow-600 py-2 rounded font-medium text-sm border-l-4 border-yellow-400">🟨 Yellow</button>
                              <button onClick={() => initiateEvent(team1Info.id, 'red_card', '🟥 Red Card')} className="bg-red-50 hover:bg-red-100 text-red-600 py-2 rounded font-medium text-sm border-l-4 border-red-500">🟥 Red</button>
                          </div>
                          <button onClick={() => initiateEvent(team1Info.id, 'substitution', '🔄 Substitution')} className="w-full bg-white hover:bg-gray-200 py-2 mt-2 rounded font-medium text-sm text-gray-800 border border-gray-200">🔄 Substitution</button>
                      </div>
                  </div>

                  {/* Team 2 Controls */}
                  <div className="bg-gray-50 p-5 rounded-lg border border-gray-200">
                      <h4 className="font-bold text-center mb-4 text-blue-700">{team2Info.name}</h4>
                      <div className="space-y-3">
                          <button onClick={() => initiateEvent(team2Info.id, 'goal', '⚽ Goal')} className="w-full bg-green-50 border-l-4 border-green-500 hover:bg-green-100 text-green-800 py-3 rounded font-bold shadow-sm flex items-center justify-center gap-2">⚽ Goal</button>
                          <button onClick={() => initiateEvent(team2Info.id, 'own_goal', '🤦‍♂️ Own Goal')} className="w-full bg-red-50 hover:bg-red-100 text-red-700 py-2 rounded font-medium text-sm flex items-center justify-center gap-2">🤦‍♂️ Own Goal (Score to {team1Info.name})</button>
                          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-gray-200">
                              <button onClick={() => initiateEvent(team2Info.id, 'yellow_card', '🟨 Yellow Card')} className="bg-yellow-50 hover:bg-yellow-100 text-yellow-600 py-2 rounded font-medium text-sm border-l-4 border-yellow-400">🟨 Yellow</button>
                              <button onClick={() => initiateEvent(team2Info.id, 'red_card', '🟥 Red Card')} className="bg-red-50 hover:bg-red-100 text-red-600 py-2 rounded font-medium text-sm border-l-4 border-red-500">🟥 Red</button>
                          </div>
                          <button onClick={() => initiateEvent(team2Info.id, 'substitution', '🔄 Substitution')} className="w-full bg-white hover:bg-gray-200 py-2 mt-2 rounded font-medium text-sm text-gray-800 border border-gray-200">🔄 Substitution</button>
                      </div>
                  </div>
              </div>
          )}
          
          <div className="border-t border-gray-300 pt-6 mt-8">
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2 text-gray-900">🎙️ Match Log</h3>
              <ul className="space-y-2">
                  {[...scores].reverse().slice(0, 10).map((s, idx) => {
                      let icon = '⏺️';
                      if (s.event_type === 'goal') icon = '⚽';
                      if (s.event_type === 'own_goal') icon = '🤦‍♂️';
                      if (s.event_type === 'yellow_card') icon = '🟨';
                      if (s.event_type === 'red_card') icon = '🟥';
                      if (s.event_type === 'substitution') icon = '🔄';

                      return (
                          <li key={idx} className="text-sm bg-gray-50 border border-gray-200 px-4 py-3 rounded flex items-center gap-3 shadow-sm">
                              <span className="font-bold text-gray-600 w-8">{s.minute}'</span> 
                              <span className="text-lg">{icon}</span>
                              <div className="flex flex-col ml-2">
                                  <span className="font-bold text-gray-800 capitalize truncate flex gap-2">
                                    {s.event_type.replace('_', ' ')}
                                  </span>
                                  {players.find(p=>p.player_id==s.player_id) && !s.event_type.includes('Substitution') && (
                                     <span className="text-gray-500 text-xs mt-0.5">{players.find(p=>p.player_id==s.player_id)?.player_name}</span>
                                  )}
                              </div>
                              <span className="text-gray-600 font-medium text-xs ml-auto">({getTeamName(s.team_id)})</span>
                          </li>
                      );
                  })}
                  {scores.length === 0 && <li className="text-gray-500 italic text-sm">No events recorded yet.</li>}
              </ul>
          </div>
       </div>
      )}
    </div>
  );
}
