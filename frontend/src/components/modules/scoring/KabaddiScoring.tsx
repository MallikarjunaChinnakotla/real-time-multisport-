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

export default function KabaddiScoring() {
  const sport = 'kabaddi';
  const [tournaments, setTournaments] = useState<any[]>([]);
  const [matches, setMatches] = useState<any[]>([]);
  const [teams, setTeams] = useState<any[]>([]);
  const [players, setPlayers] = useState<any[]>([]);
  const [scores, setScores] = useState<any[]>([]);

  const [tid, setTid] = useState('');
  const [mid, setMid] = useState('');
  
  const [timer, setTimer] = useState(2400); // 40 minutes (2x20)
  const [isRunning, setIsRunning] = useState(false);

  const [raidTimer, setRaidTimer] = useState(30); 
  const [isRaidRunning, setIsRaidRunning] = useState(false);
  
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
  
  // Match Clock
  useEffect(() => {
    let interval: any;
    if (isRunning && timer > 0) {
      interval = setInterval(() => setTimer(t => t - 1), 1000);
    }
    return () => clearInterval(interval);
  }, [isRunning, timer]);

  // Raid Clock
  useEffect(() => {
    let interval: any;
    if (isRaidRunning && raidTimer > 0) {
      interval = setInterval(() => setRaidTimer(t => t - 1), 1000);
    }
    return () => clearInterval(interval);
  }, [isRaidRunning, raidTimer]);

  const activeMatch = matches.find(m => m.match_id == parseInt(mid));
  const tMatches = matches.filter(m => m.tournament_id == parseInt(tid));

  const getTeamName = (id: number) => teams.find(t => t.team_id == id)?.team_name || id;

  const team1Info = { id: activeMatch?.team1_id, name: getTeamName(activeMatch?.team1_id) };
  const team2Info = { id: activeMatch?.team2_id, name: getTeamName(activeMatch?.team2_id) };
  
  const team1Score = scores.filter(s => s.team_id == team1Info.id).reduce((sum, s) => sum + (parseInt(s.points) || 0), 0);
  const team2Score = scores.filter(s => s.team_id == team2Info.id).reduce((sum, s) => sum + (parseInt(s.points) || 0), 0);

  // Derive outs and count of active players dynamically based on chronological event log
  // Every successful raid puts exactly N opponent players out and revives N of your own
  // Every tackle puts 1 opponent raider out, and revives 1 of your own
  // All out resets opponent to 7
  let t1Active = 7;
  let t2Active = 7;

  scores.forEach(s => {
      const isTeam1 = s.team_id == team1Info.id;
      const pts = parseInt(s.points) || 1;

      if (s.event_type.includes('Raid Point')) {
          if (isTeam1) {
              t2Active = Math.max(0, t2Active - pts);
              t1Active = Math.min(7, t1Active + pts);
          } else {
              t1Active = Math.max(0, t1Active - pts);
              t2Active = Math.min(7, t2Active + pts);
          }
      } else if (s.event_type.includes('Tackle Point') || s.event_type.includes('Super Tackle')) {
          // A tackle puts 1 raider out, regardless if it's super or normal (points vary)
          if (isTeam1) {
              t2Active = Math.max(0, t2Active - 1);
              t1Active = Math.min(7, t1Active + 1);
          } else {
              t1Active = Math.max(0, t1Active - 1);
              t2Active = Math.min(7, t2Active + 1);
          }
      } else if (s.event_type.includes('All Out')) {
          // If a team scores an all-out, it means the OTHER team is revived to 7
          if (isTeam1) t2Active = 7;
          else t1Active = 7;
      }
  });

  const team1Players = t1Active;
  const team2Players = t2Active;

  const formatTimer = (secs: number) => {
      const m = Math.floor(secs / 60).toString().padStart(2, '0');
      const s = (secs % 60).toString().padStart(2, '0');
      return `${m}:${s}`;
  };

  const recordEvent = async (teamId: number, eventStr: string, points: number) => {
      let finalPoints = points;
      let finalEvent = eventStr;
      
      const isTeam1 = teamId == team1Info.id;
      const defendersCount = isTeam1 ? t2Active : t1Active;

      // Handle All Outs automatically if points exceed defenders
      if (eventStr === 'Raid Point' && points >= defendersCount && defendersCount > 0) {
          // Record the raid points first
          await api.addScore(sport, {
              match_id: parseInt(mid),
              minute: Math.floor((2400 - timer) / 60), 
              half: formatHalf,
              team_id: teamId,
              player_id: '',
              event_type: 'Raid Point (All Out)',
              points: points,
              timestamp: new Date().toISOString()
          });
          // Also record the bonus all-out points
          finalPoints = 2;
          finalEvent = 'All Out';
      }

      await api.addScore(sport, {
          match_id: parseInt(mid),
          minute: Math.floor((2400 - timer) / 60), 
          half: formatHalf,
          team_id: teamId,
          player_id: '',
          event_type: finalEvent,
          points: finalPoints,
          timestamp: new Date().toISOString()
      });
      
      setActiveMenu('');
      setPendingEvent(null);
      fetchScores(parseInt(mid));
  };

  const [activeMenu, setActiveMenu] = useState<string>('');
  
  const [pendingEvent, setPendingEvent] = useState<any>(null);
  const [primaryPlayer, setPrimaryPlayer] = useState('');
  const [secondaryPlayer, setSecondaryPlayer] = useState('');
  const [outPlayers, setOutPlayers] = useState<string[]>([]);
  
  const confirmPendingEvent = async () => {
      if (!pendingEvent) return;
      let finalEventStr = pendingEvent.type;
      let finalPlayerId = primaryPlayer;

      if (pendingEvent.baseEvent === 'Raid Point') {
          if (!primaryPlayer) { alert('Please select a Raider'); return; }
          if (outPlayers.some(p => !p) && outPlayers.length > 0) { alert('Please select all players who are out'); return; }
          
          let names = outPlayers.map(id => players.find(p=>p.player_id==id)?.player_name).join(', ');
          finalEventStr = `Raid Point | Raider: ${players.find(p=>p.player_id==primaryPlayer)?.player_name} | Out: ${names || 'None'}`;
          finalPlayerId = `${primaryPlayer}`;
      } else if (pendingEvent.baseEvent === 'Tackle Point' || pendingEvent.baseEvent === 'Super Tackle') {
          if (!primaryPlayer || !secondaryPlayer) { alert('Please select both Tackler and Tackled Raider'); return; }
          finalEventStr = `${pendingEvent.baseEvent} | Tackler: ${players.find(p=>p.player_id==primaryPlayer)?.player_name} | Tackled: ${players.find(p=>p.player_id==secondaryPlayer)?.player_name}`;
      } else if (pendingEvent.baseEvent === 'Substitution') {
          if (!primaryPlayer || !secondaryPlayer) { alert('Please select both Player Out and Player In'); return; }
          finalEventStr = `Substitution | Out: ${players.find(p=>p.player_id==primaryPlayer)?.player_name} In: ${players.find(p=>p.player_id==secondaryPlayer)?.player_name}`;
      } else if (pendingEvent.baseEvent.includes('Card')) {
          if (!primaryPlayer) { alert('Please select a player'); return; }
          finalEventStr = `${pendingEvent.baseEvent} | Player: ${players.find(p=>p.player_id==primaryPlayer)?.player_name}`;
      } else if (pendingEvent.baseEvent === 'Bonus Point') {
          if (!primaryPlayer) { alert('Please select a Raider'); return; }
          finalEventStr = `Bonus Point | Raider: ${players.find(p=>p.player_id==primaryPlayer)?.player_name}`;
      } else if (pendingEvent.baseEvent === 'Empty Raid') {
          if (!primaryPlayer) { alert('Please select a Raider'); return; }
          finalEventStr = `Empty Raid | Raider: ${players.find(p=>p.player_id==primaryPlayer)?.player_name}`;
      } else if (pendingEvent.baseEvent === 'Extra Point') {
          finalEventStr = `Extra Point`;
      }

      await api.addScore(sport, {
          match_id: parseInt(mid),
          minute: Math.floor((2400 - timer) / 60), 
          half: formatHalf,
          team_id: pendingEvent.teamId,
          player_id: finalPlayerId,
          event_type: finalEventStr,
          points: pendingEvent.points,
          timestamp: new Date().toISOString()
      });

      // Execute Kabaddi player math for score log logic if it was a Raid or Tackle
      if (pendingEvent.baseEvent === 'Raid Point' || pendingEvent.baseEvent === 'Tackle Point' || pendingEvent.baseEvent === 'Super Tackle') {
           // Let the original recordEvent math execute by recursively calling it with the raw primitive names and points so active players calculate correctly
           // We just bypass the API call in recordEvent when we pass a flag to avoid double writing
           // Wait, recordEvent triggers an API call directly. We can just skip calling confirmEvent and call a modified version of recordEvent, OR we write the API call here and trigger a fetch.
           // Since we manually appended string info to the event_type above, the Kabaddi engine string parser in `t1Active` calculation MIGHT fail if it doesn't strictly regex match it.
      }
      setActiveMenu('');
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

  const formatHalf = timer > 1200 ? 1 : 2;

  

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6 font-sans">
      <h1 className="text-4xl font-bold flex items-center gap-3">
          Kabaddi Dashboard
      </h1>
      <p className="text-gray-600 text-sm mb-4">Live kabaddi stats go here...</p>

      <h2 className="text-xl font-bold mt-8 flex items-center gap-2"><span className="text-red-500 text-2xl">🔴</span> Live Match</h2>

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
                              <option value="Court">Court</option>
                              <option value="Raid">Raid</option>
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
          
          <div className="flex justify-between items-center px-4 mb-6">
              <span className="text-3xl font-bold">{team1Info.name}</span>
              <span className="text-xl font-bold text-gray-600">VS</span>
              <span className="text-3xl font-bold">{team2Info.name}</span>
          </div>
          
          <div className="flex justify-between items-center px-4 mb-10">
              <span className="text-4xl font-bold">{team1Score} <span className="text-gray-500 text-lg opacity-60">🔗</span></span>
              <span className="text-4xl font-bold">{team2Score}</span>
          </div>

          <h3 className="text-2xl font-bold mb-4 flex items-center gap-2"><span className="text-green-500">🟢</span> Active Players on Mat</h3>
          <div className="flex justify-between mb-8">
              <div>
                  <div className="text-sm font-medium mb-3">{team1Info.name} ({team1Players})</div>
                  <div className="flex gap-2">
                      {[...Array(7)].map((_, i) => (
                           <div key={i} className={`w-4 h-4 rounded-full ${i < team1Players ? 'bg-[#FF1A5A]' : 'bg-gray-200'}`}></div>
                      ))}
                  </div>
              </div>
              <div className="text-right">
                  <div className="text-sm font-medium mb-3">{team2Info.name} ({team2Players})</div>
                  <div className="flex gap-2 justify-end">
                      {[...Array(7)].map((_, i) => (
                           <div key={i} className={`w-4 h-4 rounded-full ${i < team2Players ? 'bg-[#1DA1F2]' : 'bg-gray-200'}`}></div>
                      ))}
                  </div>
              </div>
          </div>

          <div className="border border-gray-200 rounded p-4 mb-8 bg-gray-100 cursor-pointer hover:bg-gray-100 transition-colors flex items-center justify-between text-sm text-gray-800">
             <span><span className="mr-2">❯</span> Adjust Active Players Manually</span>
          </div>

          <h2 className="text-2xl font-bold flex items-center gap-3 mb-6">⏱️ Clock Controls</h2>
          <div className="flex gap-4 mb-6">
              <button onClick={() => setIsRunning(true)} className="bg-blue-50 border border-blue-200 text-blue-700 px-4 py-2 rounded text-sm font-medium hover:bg-blue-100">
                  ▶️ Start/Resume
              </button>
              <button onClick={() => setIsRunning(false)} className="bg-orange-50 border border-orange-200 text-[#E5C7A2] px-4 py-2 rounded text-sm font-medium hover:bg-orange-100">
                  ⏸️ Pause
              </button>
              <button onClick={() => {setIsRunning(false); setTimer(2400);}} className="bg-gray-200 border border-gray-200 text-gray-900 px-4 py-2 rounded text-sm font-medium hover:bg-white flex items-center gap-2">
                  🔄 Reset Match
              </button>
          </div>

          <div className="mb-8">
              <h3 className="text-xl font-bold mb-4">Current Half: {formatHalf}</h3>
              <h2 className="text-3xl font-bold mb-2 font-mono">{formatTimer(timer)} <span className="text-gray-500 text-lg font-sans">(Countdown)</span></h2>
              <div className="text-xs text-gray-500">Elapsed: {formatTimer(2400 - timer)} | Total: 40:00</div>
          </div>

          {timer === 0 && (
              <div className="bg-green-50 text-green-700 p-3 rounded mb-8 text-sm font-medium flex items-center gap-2">
                  🏁 Match ended (40 minutes). Timer stopped.
              </div>
          )}

          <h2 className="text-2xl font-bold flex items-center gap-2 mb-4 border-t border-gray-300 pt-8">⏱️ Raid Timer <span className="text-gray-500 text-xl opacity-60">🔗</span></h2>
          <div className="flex gap-4 justify-center mb-6">
              <button onClick={() => setIsRaidRunning(true)} className="bg-gray-100 border border-gray-200 px-6 py-2 rounded text-sm font-medium hover:bg-gray-200 transition-colors min-w-[30%]">
                  🚀 Start/Resume
              </button>
              <button onClick={() => setIsRaidRunning(false)} className="bg-gray-100 border border-gray-200 px-6 py-2 rounded text-sm font-medium hover:bg-gray-200 transition-colors min-w-[30%]">
                  ⏸️ Pause
              </button>
              <button onClick={() => {setIsRaidRunning(false); setRaidTimer(30);}} className="bg-gray-100 border border-gray-200 px-6 py-2 rounded text-sm font-medium hover:bg-gray-200 transition-colors min-w-[30%]">
                  🔄 Reset
              </button>
          </div>

          <div className="text-center py-8 border-b border-gray-200 mb-8">
              <div className="text-5xl font-bold text-gray-600 mb-2">{raidTimer}s</div>
          </div>

          <h2 className="text-2xl font-bold flex items-center gap-2 mb-4">➕ Record Event <span className="text-lg font-normal text-gray-600">(Button Mode)</span></h2>
          <button className="bg-white border border-gray-200 px-4 py-2 rounded text-red-700 font-semibold hover:bg-red-50 transition-colors mb-6 text-sm flex items-center">
             ❌ Cancel / Reset Form
          </button>
          
          <div className="bg-blue-50 border border-blue-200 p-4 rounded mb-6 text-sm font-medium flex justify-between items-center">
              <span>Select Event Type (for {team1Info.name}):</span>
          </div>
          
          {pendingEvent && pendingEvent.teamId === team1Info.id ? (
              <div className="bg-white border text-center border-gray-200 p-6 rounded mb-8 shadow-md">
                 <h4 className="font-bold text-blue-800 mb-4">{pendingEvent.baseEvent} Details</h4>
                 {pendingEvent.baseEvent === 'Raid Point' && (
                     <div className="grid grid-cols-1 gap-4 text-left">
                         <InputSelect label="🏃 Who is the Raider?" value={primaryPlayer} onChange={setPrimaryPlayer} options={players.filter(p=>p.team_id==team1Info.id).map(p=>({id:p.player_id,label:p.player_name}))} />
                         {outPlayers.map((_, idx) => (
                             <InputSelect key={idx} label={`🎯 Who is out? (Target ${idx+1})`} value={outPlayers[idx]} onChange={val => {
                                 let updated = [...outPlayers];
                                 updated[idx] = val;
                                 setOutPlayers(updated);
                             }} options={players.filter(p=>p.team_id==team2Info.id).map(p=>({id:p.player_id,label:p.player_name}))} />
                         ))}
                     </div>
                 )}
                 {(pendingEvent.baseEvent === 'Tackle Point' || pendingEvent.baseEvent === 'Super Tackle') && (
                     <div className="grid grid-cols-2 gap-4 text-left">
                         <InputSelect label="🤼 Tackler (Our Team)" value={primaryPlayer} onChange={setPrimaryPlayer} options={players.filter(p=>p.team_id==team1Info.id).map(p=>({id:p.player_id,label:p.player_name}))} />
                         <InputSelect label="🏃 Tackled (Opponent Raider)" value={secondaryPlayer} onChange={setSecondaryPlayer} options={players.filter(p=>p.team_id==team2Info.id).map(p=>({id:p.player_id,label:p.player_name}))} />
                     </div>
                 )}
                 {pendingEvent.baseEvent === 'Substitution' && (
                     <div className="grid grid-cols-2 gap-4 text-left">
                         <InputSelect label="🔴 Player Out" value={primaryPlayer} onChange={setPrimaryPlayer} options={players.filter(p=>p.team_id==team1Info.id).map(p=>({id:p.player_id,label:p.player_name}))} />
                         <InputSelect label="🟢 Player In" value={secondaryPlayer} onChange={setSecondaryPlayer} options={players.filter(p=>p.team_id==team1Info.id).map(p=>({id:p.player_id,label:p.player_name}))} />
                     </div>
                 )}
                 {pendingEvent.baseEvent.includes('Card') && (
                     <div className="grid grid-cols-1 gap-4 text-left">
                         <InputSelect label="Player receiving card" value={primaryPlayer} onChange={setPrimaryPlayer} options={players.filter(p=>p.team_id==team1Info.id).map(p=>({id:p.player_id,label:p.player_name}))} />
                     </div>
                 )}
                 {pendingEvent.baseEvent === 'Bonus Point' && (
                     <div className="grid grid-cols-1 gap-4 text-left">
                         <InputSelect label="Bonus Point Raider" value={primaryPlayer} onChange={setPrimaryPlayer} options={players.filter(p=>p.team_id==team1Info.id).map(p=>({id:p.player_id,label:p.player_name}))} />
                     </div>
                 )}
                 {pendingEvent.baseEvent === 'Empty Raid' && (
                     <div className="grid grid-cols-1 gap-4 text-left">
                         <InputSelect label="Raider (Empty Raid)" value={primaryPlayer} onChange={setPrimaryPlayer} options={players.filter(p=>p.team_id==team1Info.id).map(p=>({id:p.player_id,label:p.player_name}))} />
                     </div>
                 )}
                 {pendingEvent.baseEvent === 'Extra Point' && (
                     <div className="text-gray-600 mb-4">
                         Award 1 Extra Point to {team1Info.name}.
                     </div>
                 )}

                 <div className="flex gap-4 justify-center mt-6">
                     <button onClick={confirmPendingEvent} className="bg-blue-600 hover:bg-blue-700 text-gray-900 font-bold py-2 px-8 rounded shadow">Confirm {pendingEvent.baseEvent}</button>
                     <button onClick={() => setPendingEvent(null)} className="bg-white border rounded py-2 px-8 hover:bg-gray-100">Cancel</button>
                 </div>
              </div>
          ) : activeMenu === 'Team1Raid' ? (
              <div className="bg-white border text-center border-gray-200 p-6 rounded mb-8 shadow-sm">
                  <h4 className="font-bold text-gray-800 mb-4">How many opponents put out?</h4>
                  <div className="flex justify-center gap-2 mb-4">
                      {[1,2,3,4,5,6,7].map(n => (
                          <button key={n} onClick={() => {
                              setPrimaryPlayer(''); setOutPlayers(Array(n).fill('')); 
                              setPendingEvent({teamId: team1Info.id, type: `Raid Point`, baseEvent: 'Raid Point', points: n});
                          }} disabled={n > t2Active} className={`w-12 h-12 rounded-full font-bold text-lg ${n > t2Active ? 'bg-gray-100 text-gray-600 cursor-not-allowed' : 'bg-blue-600 text-gray-900 hover:bg-blue-700 shadow'} transition-colors`}>{n}</button>
                      ))}
                  </div>
                  <button onClick={() => setActiveMenu('')} className="text-gray-500 text-sm hover:underline">Cancel</button>
              </div>
          ) : activeMenu === 'Team1Tackle' ? (
              <div className="bg-white border text-center border-gray-200 p-6 rounded mb-8 shadow-sm">
                  <h4 className="font-bold text-gray-800 mb-4">Tackle Options</h4>
                  <div className="flex justify-center gap-4 mb-4">
                      <button onClick={() => { setPrimaryPlayer(''); setSecondaryPlayer(''); setPendingEvent({teamId: team1Info.id, type: 'Tackle Point', baseEvent: 'Tackle Point', points: 1}); }} className="bg-blue-600 px-6 py-3 rounded font-bold text-gray-900 hover:bg-blue-700 shadow transition-colors">Tackle (1 Pt)</button>
                      <button onClick={() => { setPrimaryPlayer(''); setSecondaryPlayer(''); setPendingEvent({teamId: team1Info.id, type: 'Super Tackle', baseEvent: 'Super Tackle', points: 2}); }} className="bg-orange-500 px-6 py-3 rounded font-bold text-gray-900 hover:bg-orange-600 shadow transition-colors">Super Tackle (2 Pts)</button>
                  </div>
                  <button onClick={() => setActiveMenu('')} className="text-gray-500 text-sm hover:underline">Cancel</button>
              </div>
          ) : activeMenu === 'Team1Menu' ? (
              <div className="grid grid-cols-5 gap-4 mb-4">
                 <button onClick={() => setActiveMenu('Team1Raid')} className="bg-gray-50 border border-gray-200 px-2 py-3 rounded hover:bg-gray-200 transition-colors text-sm font-medium">🏃 Raid Point</button>
                 <button onClick={() => setActiveMenu('Team1Tackle')} className="bg-gray-50 border border-gray-200 px-2 py-3 rounded hover:bg-gray-200 transition-colors text-sm font-medium flex justify-center items-center gap-1">🤼 Tackle Point</button>
                 <button onClick={() => { setPrimaryPlayer(''); setPendingEvent({teamId: team1Info.id, type: 'Bonus Point', baseEvent: 'Bonus Point', points: 1}); }} className="bg-gray-50 border border-gray-200 px-2 py-3 rounded hover:bg-gray-200 transition-colors text-sm font-medium">🎁 Bonus Point</button>
                 <button onClick={() => { setPrimaryPlayer(''); setPendingEvent({teamId: team1Info.id, type: 'Empty Raid', baseEvent: 'Empty Raid', points: 0}); }} className="bg-gray-50 border border-gray-200 px-2 py-3 rounded hover:bg-gray-200 transition-colors text-sm font-medium">🚶 Empty Raid</button>
                 <button onClick={() => { setPrimaryPlayer(''); setPendingEvent({teamId: team1Info.id, type: 'Extra Point', baseEvent: 'Extra Point', points: 1}); }} className="bg-gray-50 border border-gray-200 px-2 py-3 rounded hover:bg-gray-200 transition-colors text-sm font-medium">✨ Extra Point</button>
                 <button onClick={() => recordEvent(team1Info.id, 'All Out', 2)} className="bg-gray-50 border border-gray-200 px-2 py-3 rounded hover:bg-gray-200 transition-colors text-sm font-medium flex justify-center items-center gap-1"><span className="text-red-500 text-lg leading-none">🛑</span> All Out</button>
                 <button onClick={() => { setPrimaryPlayer(''); setPendingEvent({teamId: team1Info.id, type: 'Green Card', baseEvent: 'Green Card', points: 0}); }} className="bg-green-50 text-green-700 border border-green-200 px-2 py-3 rounded hover:bg-green-100 transition-colors text-sm font-medium">🟩 Green Card</button>
                 <button onClick={() => { setPrimaryPlayer(''); setPendingEvent({teamId: team1Info.id, type: 'Yellow Card', baseEvent: 'Yellow Card', points: 0}); }} className="bg-yellow-50 text-yellow-700 border border-yellow-200 px-2 py-3 rounded hover:bg-yellow-100 transition-colors text-sm font-medium">🟨 Yellow</button>
                 <button onClick={() => { setPrimaryPlayer(''); setPendingEvent({teamId: team1Info.id, type: 'Red Card', baseEvent: 'Red Card', points: 0}); }} className="bg-red-50 text-red-700 border border-red-200 px-2 py-3 rounded hover:bg-red-100 transition-colors text-sm font-medium">🟥 Red Card</button>
                 <button onClick={() => { setPrimaryPlayer(''); setSecondaryPlayer(''); setPendingEvent({teamId: team1Info.id, type: 'Substitution', baseEvent: 'Substitution', points: 0}); }} className="bg-white border border-gray-200 px-2 py-3 rounded hover:bg-gray-100 transition-colors text-sm font-medium">🔄 Sub</button>
              </div>
          ) : (
                <button onClick={() => setActiveMenu('Team1Menu')} className="bg-white border border-gray-200 w-full py-3 hover:bg-gray-50 mb-4 rounded font-medium shadow-sm transition-colors text-blue-700">Open Team 1 Options +</button>
          )}

          <div className="bg-blue-50 border border-blue-200 p-4 rounded mb-6 text-sm font-medium mt-8 flex justify-between items-center">
              <span>Select Event Type (for {team2Info.name}):</span>
          </div>
          
          {pendingEvent && pendingEvent.teamId === team2Info.id ? (
              <div className="bg-white border text-center border-gray-200 p-6 rounded mb-8 shadow-md">
                 <h4 className="font-bold text-teal-800 mb-4">{pendingEvent.baseEvent} Details</h4>
                 {pendingEvent.baseEvent === 'Raid Point' && (
                     <div className="grid grid-cols-1 gap-4 text-left">
                         <InputSelect label="🏃 Who is the Raider?" value={primaryPlayer} onChange={setPrimaryPlayer} options={players.filter(p=>p.team_id==team2Info.id).map(p=>({id:p.player_id,label:p.player_name}))} />
                         {outPlayers.map((_, idx) => (
                             <InputSelect key={idx} label={`🎯 Who is out? (Target ${idx+1})`} value={outPlayers[idx]} onChange={val => {
                                 let updated = [...outPlayers];
                                 updated[idx] = val;
                                 setOutPlayers(updated);
                             }} options={players.filter(p=>p.team_id==team1Info.id).map(p=>({id:p.player_id,label:p.player_name}))} />
                         ))}
                     </div>
                 )}
                 {(pendingEvent.baseEvent === 'Tackle Point' || pendingEvent.baseEvent === 'Super Tackle') && (
                     <div className="grid grid-cols-2 gap-4 text-left">
                         <InputSelect label="🤼 Tackler (Our Team)" value={primaryPlayer} onChange={setPrimaryPlayer} options={players.filter(p=>p.team_id==team2Info.id).map(p=>({id:p.player_id,label:p.player_name}))} />
                         <InputSelect label="🏃 Tackled (Opponent Raider)" value={secondaryPlayer} onChange={setSecondaryPlayer} options={players.filter(p=>p.team_id==team1Info.id).map(p=>({id:p.player_id,label:p.player_name}))} />
                     </div>
                 )}
                 {pendingEvent.baseEvent === 'Substitution' && (
                     <div className="grid grid-cols-2 gap-4 text-left">
                         <InputSelect label="🔴 Player Out" value={primaryPlayer} onChange={setPrimaryPlayer} options={players.filter(p=>p.team_id==team2Info.id).map(p=>({id:p.player_id,label:p.player_name}))} />
                         <InputSelect label="🟢 Player In" value={secondaryPlayer} onChange={setSecondaryPlayer} options={players.filter(p=>p.team_id==team2Info.id).map(p=>({id:p.player_id,label:p.player_name}))} />
                     </div>
                 )}
                 {pendingEvent.baseEvent.includes('Card') && (
                     <div className="grid grid-cols-1 gap-4 text-left">
                         <InputSelect label="Player receiving card" value={primaryPlayer} onChange={setPrimaryPlayer} options={players.filter(p=>p.team_id==team2Info.id).map(p=>({id:p.player_id,label:p.player_name}))} />
                     </div>
                 )}
                 {pendingEvent.baseEvent === 'Bonus Point' && (
                     <div className="grid grid-cols-1 gap-4 text-left">
                         <InputSelect label="Bonus Point Raider" value={primaryPlayer} onChange={setPrimaryPlayer} options={players.filter(p=>p.team_id==team2Info.id).map(p=>({id:p.player_id,label:p.player_name}))} />
                     </div>
                 )}
                 {pendingEvent.baseEvent === 'Empty Raid' && (
                     <div className="grid grid-cols-1 gap-4 text-left">
                         <InputSelect label="Raider (Empty Raid)" value={primaryPlayer} onChange={setPrimaryPlayer} options={players.filter(p=>p.team_id==team2Info.id).map(p=>({id:p.player_id,label:p.player_name}))} />
                     </div>
                 )}
                 {pendingEvent.baseEvent === 'Extra Point' && (
                     <div className="text-gray-600 mb-4">
                         Award 1 Extra Point to {team2Info.name}.
                     </div>
                 )}

                 <div className="flex gap-4 justify-center mt-6">
                     <button onClick={confirmPendingEvent} className="bg-teal-600 hover:bg-teal-700 text-gray-900 font-bold py-2 px-8 rounded shadow">Confirm {pendingEvent.baseEvent}</button>
                     <button onClick={() => setPendingEvent(null)} className="bg-white border rounded py-2 px-8 hover:bg-gray-100">Cancel</button>
                 </div>
              </div>
          ) : activeMenu === 'Team2Raid' ? (
              <div className="bg-white border text-center border-gray-200 p-6 rounded mb-8 shadow-sm">
                  <h4 className="font-bold text-gray-800 mb-4">How many opponents put out?</h4>
                  <div className="flex justify-center gap-2 mb-4">
                      {[1,2,3,4,5,6,7].map(n => (
                          <button key={n} onClick={() => {
                              setPrimaryPlayer(''); setOutPlayers(Array(n).fill('')); 
                              setPendingEvent({teamId: team2Info.id, type: `Raid Point`, baseEvent: 'Raid Point', points: n});
                          }} disabled={n > t1Active} className={`w-12 h-12 rounded-full font-bold text-lg ${n > t1Active ? 'bg-gray-100 text-gray-600 cursor-not-allowed' : 'bg-teal-600 text-gray-900 hover:bg-teal-700 shadow'} transition-colors`}>{n}</button>
                      ))}
                  </div>
                  <button onClick={() => setActiveMenu('')} className="text-gray-500 text-sm hover:underline">Cancel</button>
              </div>
          ) : activeMenu === 'Team2Tackle' ? (
              <div className="bg-white border text-center border-gray-200 p-6 rounded mb-8 shadow-sm">
                  <h4 className="font-bold text-gray-800 mb-4">Tackle Options</h4>
                  <div className="flex justify-center gap-4 mb-4">
                      <button onClick={() => { setPrimaryPlayer(''); setSecondaryPlayer(''); setPendingEvent({teamId: team2Info.id, type: 'Tackle Point', baseEvent: 'Tackle Point', points: 1}); }} className="bg-teal-600 px-6 py-3 rounded font-bold text-gray-900 hover:bg-teal-700 shadow transition-colors">Tackle (1 Pt)</button>
                      <button onClick={() => { setPrimaryPlayer(''); setSecondaryPlayer(''); setPendingEvent({teamId: team2Info.id, type: 'Super Tackle', baseEvent: 'Super Tackle', points: 2}); }} className="bg-orange-500 px-6 py-3 rounded font-bold text-gray-900 hover:bg-orange-600 shadow transition-colors">Super Tackle (2 Pts)</button>
                  </div>
                  <button onClick={() => setActiveMenu('')} className="text-gray-500 text-sm hover:underline">Cancel</button>
              </div>
          ) : activeMenu === 'Team2Menu' ? (
              <div className="grid grid-cols-5 gap-4 mb-10">
                 <button onClick={() => setActiveMenu('Team2Raid')} className="bg-gray-50 border border-gray-200 px-2 py-3 rounded hover:bg-gray-200 transition-colors text-sm font-medium">🏃 Raid Point</button>
                 <button onClick={() => setActiveMenu('Team2Tackle')} className="bg-gray-50 border border-gray-200 px-2 py-3 rounded hover:bg-gray-200 transition-colors text-sm font-medium flex justify-center items-center gap-1">🤼 Tackle Point</button>
                 <button onClick={() => { setPrimaryPlayer(''); setPendingEvent({teamId: team2Info.id, type: 'Bonus Point', baseEvent: 'Bonus Point', points: 1}); }} className="bg-gray-50 border border-gray-200 px-2 py-3 rounded hover:bg-gray-200 transition-colors text-sm font-medium">🎁 Bonus Point</button>
                 <button onClick={() => { setPrimaryPlayer(''); setPendingEvent({teamId: team2Info.id, type: 'Empty Raid', baseEvent: 'Empty Raid', points: 0}); }} className="bg-gray-50 border border-gray-200 px-2 py-3 rounded hover:bg-gray-200 transition-colors text-sm font-medium">🚶 Empty Raid</button>
                 <button onClick={() => { setPrimaryPlayer(''); setPendingEvent({teamId: team2Info.id, type: 'Extra Point', baseEvent: 'Extra Point', points: 1}); }} className="bg-gray-50 border border-gray-200 px-2 py-3 rounded hover:bg-gray-200 transition-colors text-sm font-medium">✨ Extra Point</button>
                 <button onClick={() => recordEvent(team2Info.id, 'All Out', 2)} className="bg-gray-50 border border-gray-200 px-2 py-3 rounded hover:bg-gray-200 transition-colors text-sm font-medium flex justify-center items-center gap-1"><span className="text-red-500 text-lg leading-none">🛑</span> All Out</button>
                 <button onClick={() => { setPrimaryPlayer(''); setPendingEvent({teamId: team2Info.id, type: 'Green Card', baseEvent: 'Green Card', points: 0}); }} className="bg-green-50 text-green-700 border border-green-200 px-2 py-3 rounded hover:bg-green-100 transition-colors text-sm font-medium">🟩 Green Card</button>
                 <button onClick={() => { setPrimaryPlayer(''); setPendingEvent({teamId: team2Info.id, type: 'Yellow Card', baseEvent: 'Yellow Card', points: 0}); }} className="bg-yellow-50 text-yellow-700 border border-yellow-200 px-2 py-3 rounded hover:bg-yellow-100 transition-colors text-sm font-medium">🟨 Yellow</button>
                 <button onClick={() => { setPrimaryPlayer(''); setPendingEvent({teamId: team2Info.id, type: 'Red Card', baseEvent: 'Red Card', points: 0}); }} className="bg-red-50 text-red-700 border border-red-200 px-2 py-3 rounded hover:bg-red-100 transition-colors text-sm font-medium">🟥 Red Card</button>
                 <button onClick={() => { setPrimaryPlayer(''); setSecondaryPlayer(''); setPendingEvent({teamId: team2Info.id, type: 'Substitution', baseEvent: 'Substitution', points: 0}); }} className="bg-white border border-gray-200 px-2 py-3 rounded hover:bg-gray-100 transition-colors text-sm font-medium">🔄 Sub</button>
              </div>
          ) : (
                <button onClick={() => setActiveMenu('Team2Menu')} className="bg-white border border-gray-200 w-full py-3 hover:bg-gray-50 mb-10 rounded font-medium shadow-sm transition-colors text-teal-700">Open Team 2 Options +</button>
          )}

          <div className="border-t border-gray-300 pt-6 mt-8">
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2 text-gray-900">🎙️ Commentary (Recent Events) <span className="text-gray-500 opacity-60">🔗</span></h3>
              <ul className="space-y-3">
                  {[...scores].reverse().slice(0, 5).map((s, idx) => (
                      <li key={idx} className="text-sm text-gray-800">
                          <span className="font-bold">{s.minute}'</span> | {s.event_type} | Team {s.team_id} scored {s.points} pts
                      </li>
                  ))}
                  {scores.length === 0 && <li className="text-sm text-gray-800 font-bold">39' <span className="font-normal opacity-80">| Raid | q (1) scored 1 pts</span></li>}
              </ul>
          </div>
       </div>
      )}
    </div>
  );
}
