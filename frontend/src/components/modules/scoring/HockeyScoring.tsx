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

export default function HockeyScoring() {
  const sport = 'hockey';
  const [tournaments, setTournaments] = useState<any[]>([]);
  const [matches, setMatches] = useState<any[]>([]);
  const [teams, setTeams] = useState<any[]>([]);
  const [players, setPlayers] = useState<any[]>([]);
  const [scores, setScores] = useState<any[]>([]);

  const [tid, setTid] = useState('');
  const [mid, setMid] = useState('');
  
  const [pendingEvent, setPendingEvent] = useState<any>(null);
  const [selectedPlayer, setSelectedPlayer] = useState('');
  
  const [timer, setTimer] = useState(0); 
  const [isRunning, setIsRunning] = useState(false);
  const [period, setPeriod] = useState(1); // 1, 2, 3

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

  const t1Goals = scores.filter(s => s.team_id == team1Info.id && s.event_type === 'goal').length;
  const t2Goals = scores.filter(s => s.team_id == team2Info.id && s.event_type === 'goal').length;

  const initiateEvent = (teamId: number, type: string) => {
      setPendingEvent({ teamId, type, label: type.replace(/_/g, ' ').toUpperCase() });
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
          minute: currentMinute,
          quarter: period,
          team_id: pendingEvent.teamId,
          player_id: selectedPlayer,
          event_type: `${pendingEvent.label} - ${players.find((p:any)=>p.player_id==selectedPlayer)?.player_name || 'Player'}`,
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
          🏑 Live Hockey Scoring
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
                              <option value="Push-back">Push-back</option>
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
          
          <div className="flex justify-between items-center bg-gray-100 border border-gray-200 p-6 rounded-lg mb-8 shadow-md">
             <div className="flex gap-4 items-center">
                 <div className="flex flex-col gap-2">
                     <button onClick={() => setIsRunning(true)} className="bg-blue-50 border border-blue-200 hover:bg-blue-100 text-blue-700 px-4 py-2 rounded text-sm font-medium w-full text-center shadow-inner transition-colors">▶️ Start</button>
                     <button onClick={() => setIsRunning(false)} className="bg-orange-50 border border-orange-200 hover:bg-orange-100 text-[#E5C7A2] px-4 py-2 rounded text-sm font-medium w-full text-center shadow-inner transition-colors">⏸️ Pause</button>
                 </div>
                 <div className="ml-4 text-center">
                     <div className="text-4xl font-mono font-bold text-gray-900 tracking-wider bg-white px-4 py-2 rounded border border-gray-200 shadow-inner mb-2">{formatTimer(timer)}</div>
                     <span className="text-blue-700 font-bold tracking-widest uppercase text-sm mr-4">Period {period}</span>
                     <button onClick={() => setPeriod(p => p < 3 ? p + 1 : 1)} className="text-xs text-gray-500 underline hover:text-gray-900 transition-colors">Next Period</button>
                 </div>
             </div>
             
             <div className="flex items-center gap-6 pr-8">
                 <div className="text-right">
                     <h2 className="text-2xl font-bold text-gray-800">{team1Info.name}</h2>
                 </div>
                 <div className="text-6xl font-black text-gray-900">{t1Goals}</div>
                 <div className="text-4xl font-black text-gray-600">-</div>
                 <div className="text-6xl font-black text-gray-900">{t2Goals}</div>
                 <div className="text-left">
                     <h2 className="text-2xl font-bold text-gray-800">{team2Info.name}</h2>
                 </div>
             </div>
          </div>

          <h3 className="text-xl font-bold mt-8 mb-4">Record Events</h3>
          
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
              {/* Team 1 */}
              <div className="bg-gray-50 p-5 rounded-lg border border-gray-200">
                  <h4 className="font-bold text-center mb-6 text-blue-700 border-b border-gray-200 pb-2">{team1Info.name}</h4>
                  <div className="space-y-4">
                      <button onClick={() => initiateEvent(team1Info.id, 'goal')} className="w-full bg-green-50 border border-[#2A5C46] hover:bg-green-100 text-green-700 py-4 rounded font-bold shadow-sm flex items-center justify-center gap-2 text-xl tracking-wider">🏒 GOAL</button>
                      
                      <div className="pt-2 border-t border-gray-200">
                          <span className="text-xs text-gray-500 uppercase tracking-widest font-bold block mb-2">Penalties</span>
                          <div className="grid grid-cols-2 gap-2">
                              <button onClick={() => initiateEvent(team1Info.id, 'penalty_minor')} className="bg-white hover:bg-gray-200 text-gray-800 py-2 rounded text-sm border-l-2 border-yellow-500">Minor (2 min)</button>
                              <button onClick={() => initiateEvent(team1Info.id, 'penalty_major')} className="bg-white hover:bg-gray-200 text-gray-800 py-2 rounded text-sm border-l-2 border-orange-500">Major (5 min)</button>
                              <button onClick={() => initiateEvent(team1Info.id, 'penalty_misconduct')} className="bg-white hover:bg-gray-200 text-gray-800 py-2 rounded text-sm border-l-2 border-red-500 col-span-2">Misconduct (10 min)</button>
                          </div>
                      </div>
                  </div>
              </div>

              {/* Team 2 */}
              <div className="bg-gray-50 p-5 rounded-lg border border-gray-200">
                  <h4 className="font-bold text-center mb-6 text-blue-700 border-b border-gray-200 pb-2">{team2Info.name}</h4>
                  <div className="space-y-4">
                      <button onClick={() => initiateEvent(team2Info.id, 'goal')} className="w-full bg-blue-50 border border-blue-200 hover:bg-[#2A4562] text-blue-700 py-4 rounded font-bold shadow-sm flex items-center justify-center gap-2 text-xl tracking-wider">🏒 GOAL</button>
                      
                      <div className="pt-2 border-t border-gray-200">
                          <span className="text-xs text-gray-500 uppercase tracking-widest font-bold block mb-2">Penalties</span>
                          <div className="grid grid-cols-2 gap-2">
                              <button onClick={() => initiateEvent(team2Info.id, 'penalty_minor')} className="bg-white hover:bg-gray-200 text-gray-800 py-2 rounded text-sm border-l-2 border-yellow-500">Minor (2 min)</button>
                              <button onClick={() => initiateEvent(team2Info.id, 'penalty_major')} className="bg-white hover:bg-gray-200 text-gray-800 py-2 rounded text-sm border-l-2 border-orange-500">Major (5 min)</button>
                              <button onClick={() => initiateEvent(team2Info.id, 'penalty_misconduct')} className="bg-white hover:bg-gray-200 text-gray-800 py-2 rounded text-sm border-l-2 border-red-500 col-span-2">Misconduct (10 min)</button>
                          </div>
                      </div>
                  </div>
              </div>
          </div>
          )}
          
          <div className="border-t border-gray-300 pt-6 mt-8">
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2 text-gray-900">📝 Game Log</h3>
              <ul className="space-y-2">
                  {[...scores].reverse().slice(0, 10).map((s, idx) => {
                      let icon = '⏺️';
                      if (s.event_type === 'goal') icon = '🏒';
                      if (s.event_type.includes('penalty')) icon = '🛑';

                      return (
                          <li key={idx} className="text-sm bg-gray-50 border border-gray-200 px-4 py-2 rounded flex items-center gap-3">
                              <span className="font-bold text-gray-600 w-16">P{s.quarter} - {s.minute}'</span> 
                              <span>{icon}</span>
                              <span className="font-medium text-gray-800 ml-2 capitalize">
                                  {s.event_type === 'goal' ? 'Goal' : s.event_type.replace('penalty_', 'Penalty: ')}
                              </span>
                              <span className="text-gray-500 text-xs ml-auto">({getTeamName(s.team_id)})</span>
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
