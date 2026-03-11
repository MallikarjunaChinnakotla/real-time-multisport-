import { useState, useEffect } from 'react';
import * as api from '../../../api';
import MatchSummary from './MatchSummary';

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

export default function CricketScoring() {
  const sport = 'cricket';
  const [tournaments, setTournaments] = useState<any[]>([]);
  const [matches, setMatches] = useState<any[]>([]);
  const [teams, setTeams] = useState<any[]>([]);
  const [players, setPlayers] = useState<any[]>([]);
  const [scores, setScores] = useState<any[]>([]);

  const [tid, setTid] = useState('');
  const [mid, setMid] = useState('');

  const [striker, setStriker] = useState('');
  const [nonStriker, setNonStriker] = useState('');
  const [bowler, setBowler] = useState('');

  // Coin Toss State
  const [tossCompleted, setTossCompleted] = useState(false);
  const [tossWinner, setTossWinner] = useState('');
  const [tossDecision, setTossDecision] = useState(''); // 'bat' or 'field'
  const [tossResult, setTossResult] = useState('');
  const [isTossing, setIsTossing] = useState(false);

  // Dialogs
  const [showWideDialog, setShowWideDialog] = useState(false);
  const [wideExtras, setWideExtras] = useState(1);
  const [wideBatRuns, setWideBatRuns] = useState(0);

  const [showNoBallDialog, setShowNoBallDialog] = useState(false);
  const [noBallExtras, setNoBallExtras] = useState(1);
  const [noBallBatRuns, setNoBallBatRuns] = useState(0);

  const [showByeDialog, setShowByeDialog] = useState(false);
  const [byeType, setByeType] = useState('Byes');
  const [byeRuns, setByeRuns] = useState(1);

  const [showWicketDialog, setShowWicketDialog] = useState(false);
  const [wicketType, setWicketType] = useState('Bowled');
  const [wicketOutPlayer, setWicketOutPlayer] = useState('');

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

  // Auto-resume match: when scores load, if empty, set current players to the last known state
  useEffect(() => {
      if (scores.length > 0 && !striker && !nonStriker && !bowler) {
          // Assume scores are ordered chronologically. Last element is the most recent ball.
          const lastBall = scores[scores.length - 1];
          if(lastBall) {
              setStriker(lastBall.striker || '');
              setNonStriker(lastBall.non_striker || '');
              setBowler(lastBall.bowler || '');
          }
      }
  }, [scores, striker, nonStriker, bowler]);

  const activeMatch = matches.find(m => m.match_id == parseInt(mid));
  const tMatches = matches.filter(m => m.tournament_id == parseInt(tid));

  const getTeamName = (id: number | string) => teams.find(t => t.team_id == id)?.team_name || id;

  // Determine toss-based first batting team
  let firstBattingTeamId = activeMatch?.team1_id?.toString() || '';
  if (tossWinner && tossDecision) {
      firstBattingTeamId = tossDecision === 'bat' ? tossWinner : (tossWinner == activeMatch?.team1_id ? activeMatch?.team2_id : activeMatch?.team1_id).toString();
  } else if (scores.length > 0) {
      firstBattingTeamId = scores[0].batting_team?.toString() || firstBattingTeamId;
  }

  const inn1Scores = scores.filter(s => s.batting_team?.toString() === firstBattingTeamId);
  const inn2Scores = scores.filter(s => s.batting_team?.toString() !== firstBattingTeamId && s.batting_team);

  const getInnStats = (inn: any[]) => {
      let r = 0, w = 0, b = 0;
      inn.forEach(s => {
          r += (parseInt(s.runs_bat) || 0) + (parseInt(s.extra_runs) || 0);
          if (s.wicket === 'Yes' || s.wicket === true) w++;
          if (s.counts_as_ball === 'Yes' || s.counts_as_ball === true) b++;
      });
      return { runs: r, wickets: w, balls: b };
  };

  const inn1Stats = getInnStats(inn1Scores);
  const inn2Stats = getInnStats(inn2Scores);

  const maxOvers = activeMatch?.overs_per_innings || 20;
  const maxBalls = maxOvers * 6;

  const isInn1Over = inn1Stats.wickets >= 10 || inn1Stats.balls >= maxBalls;
  const target = isInn1Over ? inn1Stats.runs + 1 : null;

  const isInn2Over = isInn1Over && (inn2Stats.wickets >= 10 || inn2Stats.balls >= maxBalls || (target && inn2Stats.runs >= target));

  const currentInnings = !isInn1Over ? 1 : (!isInn2Over ? 2 : 3);
  
  let battingTeamId = '';
  let bowlingTeamId = '';
  const team1IdStr = activeMatch?.team1_id?.toString() || '';
  const team2IdStr = activeMatch?.team2_id?.toString() || '';
  
  if (currentInnings === 1) {
      battingTeamId = firstBattingTeamId;
      bowlingTeamId = firstBattingTeamId === team1IdStr ? team2IdStr : team1IdStr;
  } else {
      battingTeamId = firstBattingTeamId === team1IdStr ? team2IdStr : team1IdStr;
      bowlingTeamId = firstBattingTeamId;
  }

  const activeScores = currentInnings === 1 ? inn1Scores : inn2Scores;

  const team1Players = players.filter(p => p.team_id == battingTeamId);
  const team2Players = players.filter(p => p.team_id == bowlingTeamId);

  // --- Calculations ---
  
  let totalRuns = 0;
  let totalWickets = 0;
  let balls_in_total = 0;

  // Stats
  let s_runs = 0, s_balls = 0;
  let ns_runs = 0, ns_balls = 0;
  let b_runs = 0, b_legal_balls = 0;

  activeScores.forEach(s => {
      const runsBat = parseInt(s.runs_bat) || 0;
      const extraRuns = parseInt(s.extra_runs) || 0;
      const isWide = s.is_wide === 'Yes' || s.is_wide === true;
      const isNoBall = s.is_no_ball === 'Yes' || s.is_no_ball === true;
      const countsAsBall = s.counts_as_ball === 'Yes' || s.counts_as_ball === true;
      const wkt = s.wicket === 'Yes' || s.wicket === true;

      totalRuns += runsBat + extraRuns;
      if (wkt) totalWickets++;
      
      if (countsAsBall) balls_in_total++;

      const isBatterFaced = !isWide; 
      if (s.striker == striker) {
          s_runs += runsBat;
          if (isBatterFaced) s_balls++;
      } else if (s.striker == nonStriker) {
          ns_runs += runsBat;
          if (isBatterFaced) ns_balls++;
      }

      if (s.bowler == bowler) {
          b_runs += runsBat + extraRuns;
          if (!isWide && !isNoBall) b_legal_balls++;
      }
  });

  const calculateCricketAwards = () => {
      const pStats: Record<string, {runs: number, wickets: number, runs_conceded: number, balls_faced: number}> = {};
      players.forEach(p => pStats[p.player_id.toString()] = {runs: 0, wickets: 0, runs_conceded: 0, balls_faced: 0});
      
      scores.forEach(s => {
          const rBat = parseInt(s.runs_bat) || 0;
          const xRuns = parseInt(s.extra_runs) || 0;
          const isWicket = s.wicket === 'Yes' || s.wicket === true;
          const isWide = s.is_wide === 'Yes' || s.is_wide === true;
          
          if (s.striker && pStats[s.striker.toString()]) {
              pStats[s.striker.toString()].runs += rBat;
              if(!isWide) pStats[s.striker.toString()].balls_faced++;
          }
          if (s.bowler && pStats[s.bowler.toString()]) {
              if (isWicket && s.wicket_type !== 'Run Out') pStats[s.bowler.toString()].wickets++;
              pStats[s.bowler.toString()].runs_conceded += (rBat + xRuns);
          }
      });

      let bestBatterId = '';
      let maxRuns = -1;
      let bestBowlerId = '';
      let maxWickets = -1;
      let minRunsConceded = 999;

      Object.keys(pStats).forEach(pid => {
          if (pStats[pid].runs > maxRuns) {
              maxRuns = pStats[pid].runs;
              bestBatterId = pid;
          }
          if (pStats[pid].wickets > maxWickets || (pStats[pid].wickets === maxWickets && pStats[pid].runs_conceded < minRunsConceded)) {
              maxWickets = pStats[pid].wickets;
              minRunsConceded = pStats[pid].runs_conceded;
              bestBowlerId = pid;
          }
      });

      const getPlayerName = (pid: string) => players.find(p=>p.player_id.toString()===pid)?.player_name || 'Unknown';
      
      let winnerName = 'Tie / Draw';
      let winMargin = 'N/A';
      if (inn2Stats.runs > inn1Stats.runs) {
          winnerName = getTeamName(firstBattingTeamId === team1IdStr ? team2IdStr : team1IdStr);
          winMargin = `${10 - inn2Stats.wickets} wickets`;
      } else if (inn1Stats.runs > inn2Stats.runs) {
          winnerName = getTeamName(firstBattingTeamId);
          winMargin = `${inn1Stats.runs - inn2Stats.runs} runs`;
      }

      return {
         winnerName,
         winMargin,
         bestPlayers: [
            { title: 'Player of the Match', name: getPlayerName(maxRuns > 30 ? bestBatterId : bestBowlerId), stat: maxRuns > 30 ? `${maxRuns} Runs` : `${maxWickets} Wickets` }, 
            { title: 'Best Batsman', name: getPlayerName(bestBatterId), stat: `${maxRuns} Runs` },
            { title: 'Best Bowler', name: getPlayerName(bestBowlerId), stat: `${maxWickets} Wickets` }
         ]
      };
  };

  const teamOversCompleted = Math.floor(balls_in_total / 6);
  const teamBallsInOver = balls_in_total % 6;
  const oversStr = `${teamOversCompleted}.${teamBallsInOver}`;
  
  const teamTotalBallsFraction = teamOversCompleted + (teamBallsInOver / 6);
  const crr = teamTotalBallsFraction > 0 ? (totalRuns / teamTotalBallsFraction).toFixed(2) : "0.00";
  const predScore = Math.floor(totalRuns * 2.5);

  const strikerSR = s_balls > 0 ? ((s_runs / s_balls) * 100).toFixed(1) : "--";
  const nonStrikerSR = ns_balls > 0 ? ((ns_runs / ns_balls) * 100).toFixed(1) : "--";
  const bowlerOversStr = `${Math.floor(b_legal_balls / 6)}.${b_legal_balls % 6}`;
  // Bowler econ calculation: total bowler runs / total bowler overs (as decimal)
  const bowlerTotalFraction = Math.floor(b_legal_balls / 6) + ((b_legal_balls % 6) / 6);
  const bowlerEcon = bowlerTotalFraction > 0 ? (b_runs / bowlerTotalFraction).toFixed(2) : "--";

  const applyBallEffects = (runsBat: number, byeRunsValue: number, countsAsBall: boolean) => {
      let isEndOver = false;
      const newBallsInTotal = countsAsBall ? teamBallsInOver + 1 : teamBallsInOver;
      if (countsAsBall && newBallsInTotal === 6) {
          isEndOver = true;
      }

      let swap = false;
      // Strike rotates logically on odd runs off bat OR off odd byes
      const totalRotationsRuns = runsBat + byeRunsValue;
      if (totalRotationsRuns % 2 !== 0) {
          swap = !swap;
      }

      if (isEndOver) {
          swap = !swap; // rotate for over end
          alert('End of over! Please select the next bowler.');
          setBowler(''); // Unset bowler to force selection
      }
      
      if (swap) {
          setStriker(prevStriker => {
              setNonStriker(prevStriker);
              return nonStriker;
          });
      }
  };

  const saveBall = async (runsBat: number, extraRuns: number, isWide: boolean, isNoBall: boolean, countsAsBall: boolean, wkt: boolean, wType: string, customOutPlayer?: string) => {
      if (!striker || !nonStriker || !bowler) {
          alert('Please select Striker, Non-Striker, and Bowler before scoring.');
          return;
      }

      const payload = {
          match_id: parseInt(mid),
          innings: currentInnings,
          over: teamBallsInOver === 5 && countsAsBall ? teamOversCompleted + 1 : teamOversCompleted,
          ball: teamBallsInOver === 5 && countsAsBall ? 0 : (countsAsBall ? teamBallsInOver + 1 : teamBallsInOver),
          striker: striker,
          non_striker: nonStriker,
          bowler: bowler,
          runs_bat: runsBat,
          extra_runs: extraRuns,
          is_wide: isWide ? 'Yes' : 'No',
          is_no_ball: isNoBall ? 'Yes' : 'No',
          counts_as_ball: countsAsBall ? 'Yes' : 'No',
          wicket: wkt ? 'Yes' : 'No',
          wicket_type: wType,
          batting_team: battingTeamId,
          timestamp: new Date().toISOString()
      };
      await api.addScore(sport, payload);
      const newScoresRes = await api.getScores(sport, parseInt(mid));
      setScores(newScoresRes.data);
      
      // Check if innings flipped due to this ball
      const checkInn1 = getInnStats(newScoresRes.data.filter((s:any) => s.batting_team?.toString() === firstBattingTeamId));
      if (currentInnings === 1 && (checkInn1.wickets >= 10 || checkInn1.balls >= maxBalls)) {
          alert(`Innings 1 Over! Target is ${checkInn1.runs + 1}`);
          setStriker('');
          setNonStriker('');
          setBowler('');
          return;
      } 
      
      // Pass byeRuns value (extraRuns) to rotation calculator ONLY if NO BAT RUNS were specified and it's a byes scenario...
      // Or safer: just pass extraRuns when batRuns is 0 
      const byesOrLegByesRuns = (runsBat === 0 && (wType === 'Byes' || wType === 'Leg Byes')) ? extraRuns : 0;
      applyBallEffects(runsBat, byesOrLegByesRuns, countsAsBall);

      if (wkt) {
          const outP = customOutPlayer || striker;
          alert(`${players.find(p=>p.player_id==outP)?.player_name || 'Batsman'} is out! Select the next batsman.`);
          if (striker === outP) setStriker('');
          else setNonStriker('');
      }
  };

  const handleStandardBall = (runs: number) => {
      saveBall(runs, 0, false, false, true, false, '');
  };

  const handleWideSubmit = () => {
      // Wides don't count as balls, don't increment bowler balls faced.
      // But like no balls, if they run, we want them to rotate strike on odd runs!
      saveBall(wideBatRuns, wideExtras, true, false, false, false, '');
      setShowWideDialog(false);
      setWideExtras(1);
      setWideBatRuns(0);
  };

  const handleNoBallSubmit = () => {
      // User requested: "do not increse the ball count for wiide ball and noball ,increase ball count for legal ball and byes and leg byes"
      saveBall(noBallBatRuns, noBallExtras, false, true, false, false, '');
      setShowNoBallDialog(false);
      setNoBallExtras(1);
      setNoBallBatRuns(0);
  };

  const handleByeSubmit = () => {
      saveBall(0, byeRuns, false, false, true, false, byeType);
      setShowByeDialog(false);
      setByeRuns(1);
  };

  const handleWicketSubmit = () => {
      // Typically wickets count as a ball unless it's somehow a stumped off wide. Assuming standard.
      const isRunOut = wicketType === 'Run Out';
      saveBall(0, 0, false, false, true, true, wicketType, isRunOut ? wicketOutPlayer : striker);
      setShowWicketDialog(false);
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
      
      // Simulate coin flip animation delay
      setTimeout(() => {
          const isHeads = Math.random() > 0.5;
          setTossResult(isHeads ? 'Heads' : 'Tails');
          
          // Randomly pick winning team
          const team1Wins = Math.random() > 0.5;
          setTossWinner(team1Wins ? activeMatch.team1_id.toString() : activeMatch.team2_id.toString());
          
          setIsTossing(false);
      }, 1000);
  };

  

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6 font-sans">
      <h1 className="text-3xl font-bold flex items-center mb-8 gap-3">
          🏏 Live Cricket Scoring
      </h1>

      <div className="grid grid-cols-2 gap-4">
          <InputSelect 
              label="Select Tournament" 
              value={tid} 
              onChange={val => {setTid(val); setMid(''); setTossCompleted(false);}} 
              options={tournaments.map(t => ({id: t.tournament_id, label: t.tournament_name}))} 
          />

          <InputSelect 
              label="Select Match" 
              value={mid} 
              onChange={val => {setMid(val); setTossCompleted(false);}} 
              options={tMatches.map(m => ({id: m.match_id, label: `Match ${m.match_id}: ${getTeamName(m.team1_id)} vs ${getTeamName(m.team2_id)}`}))} 
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
                              <option value="bat">Bat</option>
                              <option value="field">Field</option>
                          </select>
                      </div>
                  )}
              </div>
              {tossDecision && (
                  <button onClick={handleTossSubmit} className="bg-blue-600 hover:bg-blue-700 text-gray-900 font-bold py-2 px-8 rounded shadow">Start Match</button>
              )}
          </div>
      )}

      {activeMatch && tossCompleted && currentInnings < 3 && (
       <div className="mt-8 animate-fade-in">
          {/* Main Scorecard Header */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6 shadow-sm">
              <div className="flex justify-between items-center">
                  <div>
                      <div className="text-blue-600 font-bold uppercase tracking-widest text-sm mb-1 text-left">Innings {currentInnings}</div>
                      <h2 className="text-3xl font-black text-gray-800">
                          {getTeamName(battingTeamId)}
                      </h2>
                      <div className="text-5xl font-black text-blue-900 mt-2">
                          {totalRuns} <span className="text-3xl text-blue-700 font-bold">/ {totalWickets}</span>
                      </div>
                      <div className="text-lg text-gray-600 mt-1 font-medium">Overs: {oversStr} <span className="text-sm">/ {maxOvers}</span></div>
                  </div>
                  <div className="text-right">
                      {target ? (
                          <div className="text-red-700 font-bold text-xl mb-2">Target: {target}</div>
                      ) : null}
                      <div className="text-gray-700 font-medium">CRR: {crr}</div>
                      <div className="text-gray-700 font-medium">Req RR: {target && maxBalls - balls_in_total > 0 ? (((target - totalRuns) / (maxBalls - balls_in_total)) * 6).toFixed(2) : '-'}</div>
                  </div>
              </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              {/* Batter Stats */}
              <div className="bg-white border border-gray-200 rounded p-4 shadow-sm">
                  <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-3 font-semibold">Batters</h4>
                  <div className="flex justify-between mb-2">
                      <div className="font-semibold text-gray-800 flex items-center gap-2">
                          <span>* {players.find(p=>p.player_id==striker)?.player_name || 'Select Striker'}</span>
                      </div>
                      <div className="font-mono text-sm">
                          <span className="font-bold">{s_runs}</span>({s_balls}) <span className="text-gray-500 ml-2">SR: {strikerSR}</span>
                      </div>
                  </div>
                  <div className="flex justify-between">
                      <div className="font-semibold text-gray-600 flex items-center gap-2">
                          <span>{players.find(p=>p.player_id==nonStriker)?.player_name || 'Select Non-Strik.'}</span>
                      </div>
                      <div className="font-mono text-sm text-gray-600">
                          <span className="font-bold">{ns_runs}</span>({ns_balls}) <span className="text-gray-600 ml-2">SR: {nonStrikerSR}</span>
                      </div>
                  </div>
              </div>
              
              {/* Bowler Stats */}
              <div className="bg-white border border-gray-200 rounded p-4 shadow-sm">
                  <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-3 font-semibold">Bowler</h4>
                  <div className="flex justify-between">
                      <div className="font-semibold text-gray-800 flex items-center gap-2">
                          <span>🥎 {players.find(p=>p.player_id==bowler)?.player_name || 'Select Bowler'}</span>
                      </div>
                      <div className="font-mono text-sm">
                          <span className="font-bold">{b_runs}</span>-{bowlerOversStr} 
                          <span className="text-gray-500 ml-2">Econ: {bowlerEcon}</span>
                      </div>
                  </div>
              </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              <InputSelect label="Striker 🏏" value={striker} onChange={setStriker} options={team1Players.map(p => ({id: p.player_id, label: p.player_name}))} />
              <InputSelect label="Non-Striker 🏃" value={nonStriker} onChange={setNonStriker} options={team1Players.map(p => ({id: p.player_id, label: p.player_name}))} />
              <InputSelect label="Bowler ⚾" value={bowler} onChange={setBowler} options={team2Players.map(p => ({id: p.player_id, label: p.player_name}))} />
          </div>

          {!showWideDialog && !showNoBallDialog && !showByeDialog && !showWicketDialog ? (
              <div className="border-t border-gray-300 pt-6 mb-6 mt-6">
                <h3 className="text-xl font-bold flex items-center gap-2 mb-4 text-gray-900">📝 Record Ball</h3>
                <div className="flex flex-wrap gap-3 mb-6">
                    {[
                      {label: '0 Dot', val: 0},
                      {label: '1 Single', val: 1},
                      {label: '2 Double', val: 2},
                      {label: '3 Three', val: 3},
                      {label: '4 Four', val: 4},
                      {label: '6 Six', val: 6}
                    ].map((btn) => (
                        <button key={btn.val} onClick={() => handleStandardBall(btn.val)} className="bg-white hover:bg-gray-100 border border-gray-200 px-5 py-3 rounded-lg text-gray-900 font-bold shadow-sm transition-colors text-lg flex items-center">
                            {btn.val}
                        </button>
                    ))}
                </div>

                <h3 className="text-lg font-bold mb-3 text-gray-800">Extras & Wickets</h3>
                <div className="flex flex-wrap gap-3 mb-6">
                    <button onClick={() => setShowWideDialog(true)} className="bg-yellow-50 hover:bg-yellow-100 border border-yellow-200 px-5 py-2 rounded font-bold text-yellow-800 shadow-sm transition-colors">
                        Wide
                    </button>
                    <button onClick={() => setShowNoBallDialog(true)} className="bg-orange-50 hover:bg-orange-100 border border-orange-200 px-5 py-2 rounded font-bold text-orange-800 shadow-sm transition-colors">
                        No Ball
                    </button>
                    <button onClick={() => setShowByeDialog(true)} className="bg-blue-50 border border-blue-200 px-5 py-2 rounded font-bold text-blue-800 shadow-sm transition-colors">
                        Byes / L.Byes
                    </button>
                    
                    <button onClick={() => setShowWicketDialog(true)} className="bg-red-50 hover:bg-red-100 border border-red-200 px-5 py-2 rounded font-bold text-red-700 shadow-sm transition-colors ml-auto flex items-center gap-2">
                        ☝️ OUT
                    </button>
                </div>
              </div>
          ) : showWideDialog ? (
              <div className="bg-yellow-50 border border-yellow-200 p-6 rounded-lg mb-8">
                  <h3 className="text-lg font-bold text-yellow-800 mb-4">Wide Delivery</h3>
                  <div className="grid grid-cols-2 gap-4 mb-4">
                      <div>
                          <label className="block text-sm font-medium mb-2 text-yellow-900">Wide Extras Penalty</label>
                          <input type="number" min="1" value={wideExtras} onChange={e => setWideExtras(parseInt(e.target.value)||1)} className="border border-yellow-300 rounded px-3 py-2 w-full bg-white" />
                      </div>
                      <div>
                          <label className="block text-sm font-medium mb-2 text-yellow-900">Runs off Bat</label>
                          <input type="number" min="0" value={wideBatRuns} onChange={e => setWideBatRuns(parseInt(e.target.value)||0)} className="border border-yellow-300 rounded px-3 py-2 w-full bg-white" />
                      </div>
                  </div>
                  <div className="flex gap-4">
                      <button onClick={handleWideSubmit} className="bg-yellow-600 hover:bg-yellow-700 text-gray-900 font-bold py-2 px-6 rounded shadow">Confirm Wide</button>
                      <button onClick={() => setShowWideDialog(false)} className="bg-white hover:bg-gray-100 text-gray-800 font-semibold py-2 px-6 border border-gray-300 rounded">Cancel</button>
                  </div>
              </div>
          ) : showNoBallDialog ? (
              <div className="bg-orange-50 border border-orange-200 p-6 rounded-lg mb-8">
                  <h3 className="text-lg font-bold text-orange-800 mb-4">No Ball Delivery</h3>
                  <div className="grid grid-cols-2 gap-4 mb-4">
                      <div>
                          <label className="block text-sm font-medium mb-2 text-orange-900">No Ball Extras</label>
                          <input type="number" min="1" value={noBallExtras} onChange={e => setNoBallExtras(parseInt(e.target.value)||1)} className="border border-orange-300 rounded px-3 py-2 w-full bg-white" />
                      </div>
                      <div>
                          <label className="block text-sm font-medium mb-2 text-orange-900">Runs off Bat</label>
                          <input type="number" min="0" value={noBallBatRuns} onChange={e => setNoBallBatRuns(parseInt(e.target.value)||0)} className="border border-orange-300 rounded px-3 py-2 w-full bg-white" />
                      </div>
                  </div>
                  <div className="flex gap-4">
                      <button onClick={handleNoBallSubmit} className="bg-orange-600 hover:bg-orange-700 text-gray-900 font-bold py-2 px-6 rounded shadow">Confirm No Ball</button>
                      <button onClick={() => setShowNoBallDialog(false)} className="bg-white hover:bg-gray-100 text-gray-800 font-semibold py-2 px-6 border border-gray-300 rounded">Cancel</button>
                  </div>
              </div>
          ) : showByeDialog ? (
              <div className="bg-blue-50 border border-blue-200 p-6 rounded-lg mb-8">
                  <h3 className="text-lg font-bold text-blue-800 mb-4">Byes & Leg Byes Delivery</h3>
                  <div className="grid grid-cols-2 gap-4 mb-4">
                      <div>
                          <label className="block text-sm font-medium mb-2 text-blue-900">Type</label>
                          <select value={byeType} onChange={e => setByeType(e.target.value)} className="border border-blue-300 rounded px-3 py-2 w-full bg-white">
                              <option value="Byes">Byes</option>
                              <option value="Leg Byes">Leg Byes</option>
                          </select>
                      </div>
                      <div>
                          <label className="block text-sm font-medium mb-2 text-blue-900">Total Extas Run</label>
                          <input type="number" min="1" value={byeRuns} onChange={e => setByeRuns(parseInt(e.target.value)||1)} className="border border-blue-300 rounded px-3 py-2 w-full bg-white" />
                      </div>
                  </div>
                  <div className="flex gap-4">
                      <button onClick={handleByeSubmit} className="bg-blue-600 hover:bg-blue-700 text-gray-900 font-bold py-2 px-6 rounded shadow">Confirm Byes</button>
                      <button onClick={() => setShowByeDialog(false)} className="bg-white hover:bg-gray-100 text-gray-800 font-semibold py-2 px-6 border border-gray-300 rounded">Cancel</button>
                  </div>
              </div>
          ) : showWicketDialog && (
              <div className="bg-red-50 border border-red-200 p-6 rounded-lg mb-8">
                  <h3 className="text-lg font-bold text-red-800 mb-4">Wicket Details</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                      <InputSelect label="Wicket Type" value={wicketType} onChange={setWicketType} options={[{id: 'Bowled', label: 'Bowled'}, {id: 'Caught', label: 'Caught'}, {id: 'Run Out', label: 'Run Out'}, {id: 'LBW', label: 'LBW'}, {id: 'Stumped', label: 'Stumped'}]} />
                      {wicketType === 'Run Out' && (
                          <InputSelect label="Who is out?" value={wicketOutPlayer} onChange={setWicketOutPlayer} options={[{id: striker, label: `Striker (${players.find(p=>p.player_id==striker)?.player_name || 'Striker'})`}, {id: nonStriker, label: `Non-Striker (${players.find(p=>p.player_id==nonStriker)?.player_name || 'Non-Striker'})`}]} />
                      )}
                  </div>
                  <div className="flex gap-4 mt-2">
                      <button onClick={handleWicketSubmit} className="bg-red-600 hover:bg-red-700 text-gray-900 font-bold py-2 px-6 rounded shadow">Submit Wicket</button>
                      <button onClick={() => setShowWicketDialog(false)} className="bg-white hover:bg-gray-100 text-gray-800 font-semibold py-2 px-6 border border-gray-300 rounded">Cancel</button>
                  </div>
              </div>
          )}

          <div className="border-t border-gray-300 pt-6 mt-8">
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2 text-gray-900">🎙️ Commentary (Recent Balls)</h3>
              <ul className="space-y-3">
                  {[...activeScores].reverse().slice(0, 10).map((s, idx) => (
                      <li key={idx} className="text-sm bg-gray-50 border border-gray-200 px-4 py-3 rounded flex items-center shadow-sm">
                          <span className="w-12 font-bold text-gray-600 flex-shrink-0">{s.over}.{s.ball > 0 ? s.ball : 'x'}</span> 
                          <span className="mx-2 text-gray-600">|</span> 
                          <span className="text-gray-700 font-medium truncate">{players.find(p=>p.player_id==s.bowler)?.player_name || 'Unknown'} to {players.find(p=>p.player_id==s.striker)?.player_name || 'Unknown'} </span>
                          <span className="mx-2 text-gray-600">|</span> 
                          <strong className={s.wicket==='Yes' || s.wicket===true ? "text-red-600 ml-auto flex-shrink-0" : (s.runs_bat == 6 || s.runs_bat == 4) ? "text-blue-600 ml-auto flex-shrink-0" : "text-gray-900 ml-auto flex-shrink-0"}>
                              {s.wicket === 'Yes' || s.wicket === true ? `WICKET! (${s.wicket_type})` : `${s.runs_bat} runs ${parseInt(s.extra_runs) > 0 ? '(+'+s.extra_runs+' Extras)' : ''}`}
                          </strong>
                      </li>
                  ))}
                  {activeScores.length === 0 && <li className="text-gray-500 italic">No balls bowled yet.</li>}
              </ul>
          </div>
       </div>
      )}

      {activeMatch && tossCompleted && currentInnings === 3 && (
          <MatchSummary 
              sport="cricket" 
              winnerName={calculateCricketAwards().winnerName} 
              winMargin={calculateCricketAwards().winMargin} 
              bestPlayers={calculateCricketAwards().bestPlayers} 
          />
      )}
    </div>
  );
}
