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

export default function HandballScoring() {
  const sport = 'handball';
  const [tournaments, setTournaments] = useState<any[]>([]);
  const [matches, setMatches] = useState<any[]>([]);
  const [teams, setTeams] = useState<any[]>([]);
  const [players, setPlayers] = useState<any[]>([]);
  const [scores, setScores] = useState<any[]>([]);

  const [tid, setTid] = useState('');
  const [mid, setMid] = useState('');
  
  const [pendingEvent, setPendingEvent] = useState<any>(null);
  const [selectedPlayer, setSelectedPlayer] = useState('');
  
  const [timer, setTimer] = useState(1800); // 30 minutes countdown per half
  const [isRunning, setIsRunning] = useState(false);
  const [half, setHalf] = useState(1); // 1 or 2

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
  
  const formatTimer = (secs: number) => {
      const m = Math.floor(secs / 60).toString().padStart(2, '0');
      const s = (secs % 60).toString().padStart(2, '0');
      return `${m}:${s}`;
  };
  
  const elapsedMinute = Math.floor((1800 - timer) / 60) + 1; // 1 to 30

  const t1Goals = scores.filter(s => s.team_id == team1Info.id && s.event_type === 'goal').length;
  const t2Goals = scores.filter(s => s.team_id == team2Info.id && s.event_type === 'goal').length;

  const initiateEvent = (teamId: number, type: string) => {
      setPendingEvent({ teamId, type, label: type.replace(/_/g, ' ').toUpperCase() });
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
          minute: elapsedMinute,
          quarter: half, // Storing half in 'quarter' column
          team_id: pendingEvent.teamId,
          player_id: selectedPlayer,
          event_type: pendingEvent.type === 'timeout' ? pendingEvent.type : `${pendingEvent.label} - ${players.find((p:any)=>p.player_id==selectedPlayer)?.player_name || 'Player'}`,
          points: pendingEvent.type === 'goal' ? 1 : 0, 
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
          🤾 Live Handball Scoring
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
                              <option value="Throw-off">Throw-off</option>
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
          
          <div className="flex justify-between items-center bg-gray-100 p-8 rounded-lg border border-gray-200 mb-8 shadow-md">
             
             <div className="text-center w-5/12">
                 <h2 className="text-3xl font-bold text-blue-700 mb-4 uppercase tracking-wider">{team1Info.name}</h2>
                 <div className="text-red-700xl font-black text-gray-900">{t1Goals}</div>
             </div>
             
             <div className="text-center w-2/12 flex flex-col items-center border-l border-r border-gray-200 px-4">
                 <span className="text-gray-600 font-bold tracking-widest uppercase text-xs mb-2">Half {half}</span>
                 <div className="text-3xl font-mono font-bold text-[#FFCC00] mb-4">{formatTimer(timer)}</div>
                 
                 <div className="flex flex-col gap-2 w-full mt-2">
                     <button onClick={() => setIsRunning(true)} className="bg-blue-50 border border-blue-200 hover:bg-blue-100 text-blue-700 py-2 rounded text-xs font-bold transition-colors">▶ START</button>
                     <button onClick={() => setIsRunning(false)} className="bg-gray-200 border border-gray-200 hover:bg-white text-gray-900 py-2 rounded text-xs font-bold transition-colors">⏸ PAUSE</button>
                     <button onClick={() => { setIsRunning(false); setTimer(1800); setHalf(h => h === 1 ? 2 : 1); }} className="text-gray-500 text-xs mt-2 underline hover:text-gray-900">Next Half / Reset</button>
                 </div>
             </div>
             
             <div className="text-center w-5/12">
                 <h2 className="text-3xl font-bold text-blue-700 mb-4 uppercase tracking-wider">{team2Info.name}</h2>
                 <div className="text-red-700xl font-black text-gray-900">{t2Goals}</div>
             </div>
          </div>

          <h3 className="text-xl font-bold mt-8 mb-4">Record Match Events</h3>

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
              <div className="grid grid-cols-2 gap-8">
                  {/* Team 1 Controls */}
                  <div className="bg-gray-50 p-5 rounded-lg border border-gray-200 shadow-inner">
                      <h4 className="font-bold text-center mb-6 text-blue-700 border-b border-gray-200 pb-2">{team1Info.name}</h4>
                      
                      <button onClick={() => initiateEvent(team1Info.id, 'goal')} className="w-full bg-green-50 hover:bg-green-100 border border-[#2A5C46] text-green-700 py-4 rounded font-black shadow-sm flex items-center justify-center gap-2 text-2xl tracking-wider mb-6">🤾 GOAL +1</button>
                      
                      <span className="text-xs text-gray-500 uppercase tracking-widest font-bold block mb-3">Discipline</span>
                      <div className="grid grid-cols-3 gap-2 mb-6 text-sm">
                          <button onClick={() => initiateEvent(team1Info.id, 'yellow_card')} className="bg-white hover:bg-yellow-50 text-yellow-400 py-2 rounded font-medium border border-gray-200">🟨 Yellow</button>
                          <button onClick={() => initiateEvent(team1Info.id, 'two_min_suspension')} className="bg-white hover:bg-red-100 text-orange-400 py-2 rounded font-medium border border-gray-200">✌️ 2 Min</button>
                          <button onClick={() => initiateEvent(team1Info.id, 'red_card')} className="bg-white hover:bg-red-50 text-red-500 py-2 rounded font-medium border border-gray-200">🟥 Red</button>
                      </div>
                      
                      <span className="text-xs text-gray-500 uppercase tracking-widest font-bold block mb-3">Stats & Plays</span>
                      <div className="grid grid-cols-3 gap-2 text-sm">
                          <button onClick={() => initiateEvent(team1Info.id, 'timeout')} className="bg-white hover:bg-gray-200 text-gray-800 py-2 rounded font-medium border border-gray-200">⏱ TO</button>
                          <button onClick={() => initiateEvent(team1Info.id, 'turnover')} className="bg-white hover:bg-gray-200 text-gray-800 py-2 rounded font-medium border border-gray-200">🔄 TOV</button>
                          <button onClick={() => initiateEvent(team1Info.id, 'save')} className="bg-white hover:bg-gray-200 text-gray-800 py-2 rounded font-medium border border-gray-200">🧤 Save</button>
                      </div>
                  </div>

                  {/* Team 2 Controls */}
                  <div className="bg-gray-50 p-5 rounded-lg border border-gray-200 shadow-inner">
                      <h4 className="font-bold text-center mb-6 text-blue-700 border-b border-gray-200 pb-2">{team2Info.name}</h4>
                      
                      <button onClick={() => initiateEvent(team2Info.id, 'goal')} className="w-full bg-blue-50 hover:bg-blue-100 border border-[#2A5C62] text-blue-700 py-4 rounded font-black shadow-sm flex items-center justify-center gap-2 text-2xl tracking-wider mb-6">🤾 GOAL +1</button>
                      
                      <span className="text-xs text-gray-500 uppercase tracking-widest font-bold block mb-3">Discipline</span>
                      <div className="grid grid-cols-3 gap-2 mb-6 text-sm">
                          <button onClick={() => initiateEvent(team2Info.id, 'yellow_card')} className="bg-white hover:bg-yellow-50 text-yellow-400 py-2 rounded font-medium border border-gray-200">🟨 Yellow</button>
                          <button onClick={() => initiateEvent(team2Info.id, 'two_min_suspension')} className="bg-white hover:bg-red-100 text-orange-400 py-2 rounded font-medium border border-gray-200">✌️ 2 Min</button>
                          <button onClick={() => initiateEvent(team2Info.id, 'red_card')} className="bg-white hover:bg-red-50 text-red-500 py-2 rounded font-medium border border-gray-200">🟥 Red</button>
                      </div>
                      
                      <span className="text-xs text-gray-500 uppercase tracking-widest font-bold block mb-3">Stats & Plays</span>
                      <div className="grid grid-cols-3 gap-2 text-sm">
                          <button onClick={() => initiateEvent(team2Info.id, 'timeout')} className="bg-white hover:bg-gray-200 text-gray-800 py-2 rounded font-medium border border-gray-200">⏱ TO</button>
                          <button onClick={() => initiateEvent(team2Info.id, 'turnover')} className="bg-white hover:bg-gray-200 text-gray-800 py-2 rounded font-medium border border-gray-200">🔄 TOV</button>
                          <button onClick={() => initiateEvent(team2Info.id, 'save')} className="bg-white hover:bg-gray-200 text-gray-800 py-2 rounded font-medium border border-gray-200">🧤 Save</button>
                      </div>
                  </div>
              </div>
          )}
          
          <div className="border-t border-gray-300 pt-6 mt-8">
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2 text-gray-900">📝 Event Timeline</h3>
              <ul className="space-y-2">
                  {[...scores].reverse().slice(0, 8).map((s, idx) => {
                      let icon = '⏺️';
                      let color = 'text-gray-800';
                      if (s.event_type === 'goal') { icon = '🤾'; color = 'text-gray-900 font-bold'; }
                      if (s.event_type === 'yellow_card') icon = '🟨';
                      if (s.event_type === 'red_card') icon = '🟥';
                      if (s.event_type === 'two_min_suspension') icon = '✌️';
                      if (s.event_type === 'timeout') icon = '⏱';
                      if (s.event_type === 'turnover') icon = '🔄';
                      if (s.event_type === 'save') icon = '🧤';

                      return (
                          <li key={idx} className="text-sm bg-gray-50 border border-gray-200 px-4 py-3 rounded flex items-center gap-3">
                              <span className="font-bold text-gray-600 w-16">H{s.quarter} {s.minute}'</span> 
                              <span>{icon}</span>
                              <span className={`ml-2 capitalize ${color}`}>
                                  {s.event_type.replace(/_/g, ' ')}
                              </span>
                              <span className="text-gray-500 text-xs ml-auto uppercase font-bold tracking-wider">{getTeamName(s.team_id)}</span>
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
