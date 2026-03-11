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

export default function SoftballScoring() {
  const sport = 'softball';
  const [tournaments, setTournaments] = useState<any[]>([]);
  const [matches, setMatches] = useState<any[]>([]);
  const [teams, setTeams] = useState<any[]>([]);
  const [players, setPlayers] = useState<any[]>([]);
  const [scores, setScores] = useState<any[]>([]);

  const [tid, setTid] = useState('');
  const [mid, setMid] = useState('');
  
  const [currentInning, setCurrentInning] = useState(1);
  const [halfInning, setHalfInning] = useState<'Top' | 'Bottom'>('Top');

  const [pendingEvent, setPendingEvent] = useState<any>(null);
  const [selectedPlayer, setSelectedPlayer] = useState('');

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
  
  const activeMatch = matches.find(m => m.match_id == parseInt(mid));
  const tMatches = matches.filter(m => m.tournament_id == parseInt(tid));

  const getTeamName = (id: number) => teams.find(t => t.team_id == id)?.team_name || id;

  const team1Info = { id: activeMatch?.team1_id, name: getTeamName(activeMatch?.team1_id) };
  const team2Info = { id: activeMatch?.team2_id, name: getTeamName(activeMatch?.team2_id) };

  // Calculate generic score
  const t1Score = scores.filter(s => s.team_id == team1Info.id && s.event_type === 'run').length;
  const t2Score = scores.filter(s => s.team_id == team2Info.id && s.event_type === 'run').length;

  const outsThisInning = scores.filter(s => s.event_type === 'out' && parseInt(s.quarter) === currentInning && s.minute === (halfInning === 'Top' ? 1 : 2)).length;
  const dispOuts = outsThisInning % 3; // Reset display for UI though usually we progress

  const initiateEvent = (teamId: number, eventStr: string = 'run') => {
      setPendingEvent({ teamId, type: eventStr, label: eventStr.replace(/_/g, ' ').toUpperCase() });
      setSelectedPlayer('');
  };

  const confirmEvent = async () => {
      if(!pendingEvent) return;
      if(!selectedPlayer && pendingEvent.type !== 'out') {
          alert("Please select a player who scored/performed the action.");
          return;
      }

      await api.addScore(sport, {
          match_id: parseInt(mid),
          minute: halfInning === 'Top' ? 1 : 2, // 1 for Top, 2 for Bottom
          quarter: currentInning, // storing Inning in quarter
          team_id: pendingEvent.teamId,
          player_id: selectedPlayer,
          event_type: pendingEvent.type === 'out' ? pendingEvent.type : `${pendingEvent.label} - ${players.find((p:any)=>p.player_id==selectedPlayer)?.player_name || 'Player'}`,
          points: pendingEvent.type === 'run' || pendingEvent.type === 'home_run' ? 1 : 0, 
          timestamp: new Date().toISOString()
      });
      setPendingEvent(null);
      fetchScores(parseInt(mid));
  };

  const advanceInning = () => {
      if (halfInning === 'Top') {
          setHalfInning('Bottom');
      } else {
          setHalfInning('Top');
          setCurrentInning(c => c + 1);
      }
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
          🥎 Live Softball Scoring
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
                              <option value="Bat">Bat</option>
                              <option value="Field">Field</option>
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
          
          <div className="flex justify-between items-center bg-gray-100 p-8 rounded-lg border border-gray-200 mb-8 relative overflow-hidden">
             
             <div className="text-center w-1/3 z-10">
                 <h2 className="text-2xl font-bold text-gray-800 mb-2">{team1Info.name} <span className="text-xs text-gray-500">(Away)</span></h2>
                 <div className="text-6xl font-black text-gray-900">{t1Score}</div>
             </div>
             
             <div className="text-center w-1/3 z-10 flex flex-col items-center">
                 <div className="bg-white border border-gray-200 px-4 py-2 rounded-lg inline-block mb-3 shadow">
                     <span className="text-blue-700 font-bold tracking-widest uppercase text-sm">{halfInning} {currentInning}</span>
                 </div>
                 <div className="flex gap-2 mb-2">
                     <div className={`w-3 h-3 rounded-full ${dispOuts >= 1 ? 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)]' : 'bg-gray-700'}`}></div>
                     <div className={`w-3 h-3 rounded-full ${dispOuts >= 2 ? 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)]' : 'bg-gray-700'}`}></div>
                     <div className="w-3 h-3 rounded-full bg-gray-700 opacity-20"></div> {/* 3rd out ends it */}
                 </div>
                 <span className="text-xs text-red-400 font-bold uppercase tracking-wider">{dispOuts} Outs</span>
             </div>
             
             <div className="text-center w-1/3 z-10">
                 <h2 className="text-2xl font-bold text-gray-800 mb-2">{team2Info.name} <span className="text-xs text-gray-500">(Home)</span></h2>
                 <div className="text-6xl font-black text-gray-900">{t2Score}</div>
             </div>
          </div>

          <div className="flex justify-center mb-10">
              <button onClick={advanceInning} className="bg-white hover:bg-gray-200 border border-gray-200 px-6 py-2 rounded text-blue-700 font-medium text-sm transition-colors shadow">
                  ⏩ Advance Inning
              </button>
          </div>

          {pendingEvent ? (
              <div className="bg-white border border-blue-200 rounded-lg p-6 mb-8 shadow-md text-center">
                  <h4 className="text-xl font-bold mb-4 text-blue-800">
                      Who scored/performed the {pendingEvent.label}?
                  </h4>
                  {pendingEvent.type !== 'out' && (
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
              <div className="bg-gray-50 p-5 rounded-lg border border-gray-200">
                  <h4 className="font-bold text-center mb-4 text-blue-700">{team1Info.name} <span className="opacity-50">(Batting Top)</span></h4>
                  <div className="space-y-3">
                      <button onClick={() => initiateEvent(team1Info.id, 'run')} className="w-full bg-blue-50 border-l-4 border-blue-500 hover:bg-blue-100 text-blue-800 py-4 rounded font-bold shadow-sm flex items-center justify-center gap-2 text-xl">+1 Run</button>
                      <button onClick={() => initiateEvent(team1Info.id, 'out')} className="w-full bg-red-50 border-l-4 border-red-500 hover:bg-red-100 text-red-700 py-3 rounded font-bold text-lg flex items-center justify-center gap-2">Out</button>
                  </div>
              </div>

              <div className="bg-gray-50 p-5 rounded-lg border border-gray-200">
                  <h4 className="font-bold text-center mb-4 text-blue-700">{team2Info.name} <span className="opacity-50">(Batting Bottom)</span></h4>
                  <div className="space-y-3">
                      <button onClick={() => initiateEvent(team2Info.id, 'run')} className="w-full bg-blue-50 border-l-4 border-blue-500 hover:bg-blue-100 text-blue-800 py-4 rounded font-bold shadow-sm flex items-center justify-center gap-2 text-xl">+1 Run</button>
                      <button onClick={() => initiateEvent(team2Info.id, 'out')} className="w-full bg-red-50 border-l-4 border-red-500 hover:bg-red-100 text-red-700 py-3 rounded font-bold text-lg flex items-center justify-center gap-2">Out</button>
                  </div>
              </div>
          </div>
          )}

          <h3 className="text-xl font-bold mt-8 mb-4">Record Play</h3>
          <div className="grid grid-cols-4 gap-3">
              <button onClick={() => initiateEvent(halfInning === 'Top' ? team1Info.id : team2Info.id, 'single')} className="bg-white hover:bg-gray-200 border border-gray-200 py-2 rounded text-sm text-gray-800">Single</button>
              <button onClick={() => initiateEvent(halfInning === 'Top' ? team1Info.id : team2Info.id, 'double')} className="bg-white hover:bg-gray-200 border border-gray-200 py-2 rounded text-sm text-gray-800">Double</button>
              <button onClick={() => initiateEvent(halfInning === 'Top' ? team1Info.id : team2Info.id, 'triple')} className="bg-white hover:bg-gray-200 border border-gray-200 py-2 rounded text-sm text-gray-800">Triple</button>
              <button onClick={() => initiateEvent(halfInning === 'Top' ? team1Info.id : team2Info.id, 'home_run')} className="bg-green-50 hover:bg-green-100 border border-gray-200 py-2 rounded text-sm font-bold text-green-700">Home Run</button>
              <button onClick={() => initiateEvent(halfInning === 'Top' ? team1Info.id : team2Info.id, 'walk')} className="bg-white hover:bg-gray-200 border border-gray-200 py-2 rounded text-sm text-gray-800 col-span-2">Walk / BB</button>
              <button onClick={() => initiateEvent(halfInning === 'Top' ? team1Info.id : team2Info.id, 'strikeout')} className="bg-white hover:bg-gray-200 border border-gray-200 py-2 rounded text-sm text-gray-800 col-span-2">Strikeout (K)</button>
          </div>
       </div>
      )}
    </div>
  );
}
