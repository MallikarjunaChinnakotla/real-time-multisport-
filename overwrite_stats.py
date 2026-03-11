import os

file_path = r"c:\Users\DELL\OneDrive\Desktop\pro\frontend\src\components\modules\Stats.tsx"

content = """import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import * as api from '../../api';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function Stats() {
  const { sport } = useParams<{ sport: string }>();
  const [stats, setStats] = useState<any>(null);
  
  const [tid, setTid] = useState('');
  const [mid, setMid] = useState('');

  useEffect(() => {
    const fetchStats = async () => {
      if (!sport) return;
      try {
          const res = await api.getStats(sport);
          setStats(res.data);
      } catch (e) {
          console.error(e);
      }
    };
    fetchStats();
  }, [sport]);

  if (!stats) return (
       <div className="space-y-6 bg-white p-6 rounded-lg shadow-sm border border-gray-200 animate-pulse">
           <div className="h-6 w-48 bg-gray-200 mb-6 rounded"></div>
           <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
               <div className="h-24 bg-gray-100 rounded-lg"></div>
               <div className="h-24 bg-gray-100 rounded-lg"></div>
               <div className="h-24 bg-gray-100 rounded-lg"></div>
           </div>
       </div>
  );

  const tournamentIds = Array.from(new Set((stats.matches || []).map((m: any) => m.tournament_id)));
  const activeTournaments = stats.tournaments 
      ? stats.tournaments.filter((t: any) => tournamentIds.includes(t.tournament_id))
      : tournamentIds.map(id => stats.matches.find((m: any) => m.tournament_id === id));
  
  const availableMatches = stats.matches?.filter((m: any) => m.tournament_id == tid) || [];
  const activeMatch = stats.matches?.find((m: any) => m.match_id == mid);

  const getTeamName = (id: any) => stats.teams?.find((t: any) => t.team_id == id)?.team_name || `Team ${id}`;

  let chartData: any[] = [];
  let kabaddiStats = null;
  let quarterData: any[] = [];
  
  // Cricket Specifics
  let battingStatsTeam1: any[] = [];
  let battingStatsTeam2: any[] = [];
  let bestPlayer: any = null;
  let bestBowler: any = null;
  let top3Performers: any[] = [];
  let cricketPerOverData: any[] = [];

  if (activeMatch && stats.scores) {
      const matchScores = stats.scores.filter((s: any) => s.match_id == mid);
      let t1Score = 0;
      let t2Score = 0;
      const t1Id = activeMatch.team1_id;
      const t2Id = activeMatch.team2_id;

      if (sport === 'cricket') {
          let tempT1Chart: Record<number, number> = { 0: 0 };
          let tempT2Chart: Record<number, number> = { 0: 0 };
          let t1OverRuns: Record<number, number> = {};
          let t2OverRuns: Record<number, number> = {};
          
          const playerStats: Record<string, any> = {};
          const ensurePlayer = (p: string) => {
              if (!p) return;
              if (!playerStats[p]) {
                  playerStats[p] = { name: p, runs: 0, balls: 0, outs: 0, wickets: 0, catches: 0, balls_bowled: 0, runs_conceded: 0 };
              }
          };

          matchScores.forEach((s: any) => {
              const isT1 = s.batting_team == t1Id;
              const isT2 = s.batting_team == t2Id;
              let runs = parseInt(s.runs_bat) || 0;
              let extras = parseInt(s.extra_runs) || 0;
              let ballNum = parseFloat(s.ball) || 0;
              let theOver = Math.floor(ballNum);

              ensurePlayer(s.striker);
              ensurePlayer(s.bowler);
              
              if (s.striker) {
                   playerStats[s.striker].runs += runs;
                   if (s.extra_type !== 'Wide') playerStats[s.striker].balls += 1;
              }
              if (s.bowler) {
                   playerStats[s.bowler].runs_conceded += (runs + extras);
                   if (s.extra_type !== 'Wide' && s.extra_type !== 'No Ball') playerStats[s.bowler].balls_bowled += 1;
              }
              if (s.wicket === 'Yes' || s.wicket === '1') {
                   if (s.player_out) ensurePlayer(s.player_out);
                   if (s.player_out && playerStats[s.player_out]) playerStats[s.player_out].outs += 1;
                   if (s.bowler && s.wicket_type !== 'Run Out') playerStats[s.bowler].wickets += 1;
              }

              let increment = runs + extras;
              if (isT1) {
                  t1Score += increment;
                  tempT1Chart[theOver] = Math.max(tempT1Chart[theOver] || 0, t1Score);
                  t1OverRuns[theOver] = (t1OverRuns[theOver] || 0) + increment;
              }
              if (isT2) {
                  t2Score += increment;
                  tempT2Chart[theOver] = Math.max(tempT2Chart[theOver] || 0, t2Score);
                  t2OverRuns[theOver] = (t2OverRuns[theOver] || 0) + increment;
              }
          });

          const maxOver = Math.max(...Object.keys(tempT1Chart).map(Number), ...Object.keys(tempT2Chart).map(Number), 0);
          for (let i = 0; i <= maxOver; i++) {
              chartData.push({
                  name: `Over ${i+1}`,
                  [getTeamName(t1Id)]: tempT1Chart[i] !== undefined ? tempT1Chart[i] : chartData[i-1]?.[getTeamName(t1Id)] || 0,
                  [getTeamName(t2Id)]: tempT2Chart[i] !== undefined ? tempT2Chart[i] : chartData[i-1]?.[getTeamName(t2Id)] || 0,
              });
              cricketPerOverData.push({
                  name: `Over ${i+1}`,
                  [getTeamName(t1Id)]: t1OverRuns[i] || 0,
                  [getTeamName(t2Id)]: t2OverRuns[i] || 0
              });
          }
          
          chartData = [{ name: 'Start', [getTeamName(t1Id)]: 0, [getTeamName(t2Id)]: 0 }, ...chartData];

          let allPerformers = Object.values(playerStats).map((p: any) => {
              let strike_rate = p.balls > 0 ? (p.runs / p.balls) * 100 : 0;
              let overs = p.balls_bowled / 6.0;
              let economy = overs > 0 ? (p.runs_conceded / overs) : 0;
              let mvp_score = (p.runs * 1.2) + (p.wickets * 15) + (p.catches * 8) + ((strike_rate - 100) / 5.0) - ((economy - 6.0) * 2.0);
              return { ...p, strike_rate, economy, mvp_score };
          });

          allPerformers.sort((a, b) => b.mvp_score - a.mvp_score);
          top3Performers = allPerformers.slice(0, 3);
          if (allPerformers.length > 0) bestPlayer = allPerformers[0];
          let bowlers = allPerformers.filter(p => p.balls_bowled > 0).sort((a, b) => b.wickets - a.wickets || a.economy - b.economy);
          if (bowlers.length > 0) bestBowler = bowlers[0];

          const t1Players = new Set(matchScores.filter((s:any) => s.batting_team == t1Id).map((s:any) => s.striker));
          const t2Players = new Set(matchScores.filter((s:any) => s.batting_team == t2Id).map((s:any) => s.striker));
          battingStatsTeam1 = allPerformers.filter(p => t1Players.has(p.name)).map((p, i) => ({ ...p, id: i }));
          battingStatsTeam2 = allPerformers.filter(p => t2Players.has(p.name)).map((p, i) => ({ ...p, id: i }));

      } else {
          // Generic Sports Data Parsing
          chartData = matchScores.map((s: any, index: number) => {
              const isT1 = s.team_id == t1Id || s.batting_team == t1Id;
              const isT2 = s.team_id == t2Id || s.batting_team == t2Id;
              
              let increment = 0;
              if (s.event_type !== 'out' && s.event_type !== 'timeout' && s.event_type !== 'yellow_card' && s.event_type !== 'red_card' && s.event_type !== 'green_card' && s.event_type !== 'two_min_suspension' && s.event_type !== 'foul' && s.event_type !== 'turnover' && s.event_type !== 'save') {
                  increment = parseInt(s.points) || 1;
              }

              if (isT1) t1Score += increment;
              if (isT2) t2Score += increment;

              return {
                  name: `Score ${index + 1}`,
                  [getTeamName(t1Id)]: t1Score,
                  [getTeamName(t2Id)]: t2Score,
                  t1Inc: isT1 ? increment : 0,
                  t2Inc: isT2 ? increment : 0
              };
          });
          
          chartData = [
              { name: 'Start', [getTeamName(t1Id)]: 0, [getTeamName(t2Id)]: 0, t1Inc: 0, t2Inc: 0 },
              ...chartData
          ];

          if (sport === 'kabaddi') {
              let totalRaids = 0, successfulRaids = 0, emptyRaids = 0;
              let tacklePoints = 0, totalTackles = 0, successfulTackles = 0;
              matchScores.forEach((s: any) => {
                  const pts = parseInt(s.points) || 0;
                  if (s.event_type === 'raid') {
                       totalRaids++;
                       if (pts > 0) successfulRaids++;
                  }
                  if (s.event_type === 'empty_raid') {
                       totalRaids++;
                       emptyRaids++;
                  }
                  if (s.event_type === 'tackle' || s.event_type === 'super_tackle') {
                       totalTackles++;
                       if (pts > 0) successfulTackles++;
                       tacklePoints += pts;
                  }
              });
              kabaddiStats = {
                  totalRaids, successfulRaids, emptyRaids, tacklePoints, totalTackles, successfulTackles,
                  raidSuccess: totalRaids ? ((successfulRaids/totalRaids)*100).toFixed(1) : 0,
                  tackleSuccess: totalTackles ? ((successfulTackles/totalTackles)*100).toFixed(1) : 0
              };
          }

          if (sport === 'kabaddi' || sport === 'basketball' || sport === 'table_tennis') {
              const numQuarters = sport === 'table_tennis' ? 3 : 4;
              const chunkLabel = sport === 'kabaddi' ? 'Half/Quarter' : sport === 'table_tennis' ? 'Set' : 'Quarter';
              const dataOnly = chartData.slice(1);
              const chunkSize = Math.ceil(dataOnly.length / numQuarters) || 1;
              const t1Name = getTeamName(t1Id);
              const t2Name = getTeamName(t2Id);

              for (let i = 0; i < numQuarters; i++) {
                  const chunk = dataOnly.slice(i * chunkSize, (i + 1) * chunkSize);
                  let t1QScore = 0;
                  let t2QScore = 0;
                  chunk.forEach((c: any) => {
                      t1QScore += c.t1Inc;
                      t2QScore += c.t2Inc;
                  });
                  quarterData.push({
                      name: `${chunkLabel} ${i+1}`,
                      [t1Name]: t1QScore,
                      [t2Name]: t2QScore
                  });
              }
          }
      }
  }

  return (
    <div className="space-y-6 animate-fade-in font-sans">
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <h3 className="text-xl font-bold mb-6 text-gray-800 border-b border-gray-200 pb-3 flex items-center gap-2">
            📊 Match Performance & Analytics
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div className="bg-gray-50 border border-gray-200 p-4 rounded-lg">
                <label className="block text-sm font-bold text-gray-600 uppercase tracking-widest mb-3">Select Tournament</label>
                <select 
                    className="w-full border border-gray-300 rounded shadow-sm py-2 px-3 text-gray-800 outline-none focus:ring-2 focus:ring-blue-500 bg-white" 
                    value={tid} 
                    onChange={e => {setTid(e.target.value); setMid('');}}
                >
                    <option value="">-- Choose Tournament --</option>
                    {activeTournaments.map((t: any, i: number) => (
                        <option key={i} value={t?.tournament_id || t}>Tournament {t?.tournament_name || `#${t?.tournament_id || t}`}</option>
                    ))}
                </select>
            </div>
            <div className="bg-gray-50 border border-gray-200 p-4 rounded-lg">
                <label className="block text-sm font-bold text-gray-600 uppercase tracking-widest mb-3">Select Match</label>
                <select 
                    className="w-full border border-gray-300 rounded shadow-sm py-2 px-3 text-gray-800 outline-none focus:ring-2 focus:ring-blue-500 bg-white disabled:bg-gray-100 disabled:text-gray-400" 
                    value={mid} 
                    onChange={e => setMid(e.target.value)}
                    disabled={!tid}
                >
                    <option value="">-- Choose Match --</option>
                    {availableMatches.map((m: any) => (
                        <option key={m.match_id} value={m.match_id}>
                            Match #{m.match_id}: {getTeamName(m.team1_id)} vs {getTeamName(m.team2_id)}
                        </option>
                    ))}
                </select>
            </div>
        </div>

        {mid && chartData.length > 0 ? (
            <div className="mt-8 pt-6 border-t border-gray-100">
                
                {/* Cricket Specific Blocks */}
                {sport === 'cricket' && (
                    <div className="space-y-8 mb-8">
                        {/* Batting Summaries */}
                        <div>
                           <h3 className="text-lg font-bold mb-3 text-gray-800 flex items-center gap-2">🏏 Batting Summary - {getTeamName(activeMatch.team1_id)}</h3>
                           <div className="bg-white border border-gray-200 rounded overflow-hidden shadow-sm">
                               <table className="w-full text-sm text-left">
                                   <thead className="bg-gray-50 text-gray-600 border-b border-gray-200">
                                       <tr>
                                           <th className="px-4 py-3">Batter</th>
                                           <th className="px-4 py-3">Runs</th>
                                           <th className="px-4 py-3">Balls</th>
                                           <th className="px-4 py-3">Outs</th>
                                           <th className="px-4 py-3">Strike Rate</th>
                                           <th className="px-4 py-3">Average</th>
                                       </tr>
                                   </thead>
                                   <tbody className="divide-y divide-gray-100">
                                       {battingStatsTeam1.map((p: any, i) => (
                                           <tr key={i} className="hover:bg-gray-50">
                                               <td className="px-4 py-2 font-medium text-gray-800">{p.name}</td>
                                               <td className="px-4 py-2 text-gray-700">{p.runs}</td>
                                               <td className="px-4 py-2 text-gray-700">{p.balls}</td>
                                               <td className="px-4 py-2 text-gray-700">{p.outs}</td>
                                               <td className="px-4 py-2 text-gray-700">{p.strike_rate.toFixed(2)}</td>
                                               <td className="px-4 py-2 text-gray-700">{p.outs > 0 ? (p.runs / p.outs).toFixed(2) : p.runs}</td>
                                           </tr>
                                       ))}
                                   </tbody>
                               </table>
                           </div>
                        </div>

                        <div>
                           <h3 className="text-lg font-bold mb-3 text-gray-800 flex items-center gap-2">🏏 Batting Summary - {getTeamName(activeMatch.team2_id)}</h3>
                           <div className="bg-white border border-gray-200 rounded overflow-hidden shadow-sm">
                               <table className="w-full text-sm text-left">
                                   <thead className="bg-gray-50 text-gray-600 border-b border-gray-200">
                                       <tr>
                                           <th className="px-4 py-3">Batter</th>
                                           <th className="px-4 py-3">Runs</th>
                                           <th className="px-4 py-3">Balls</th>
                                           <th className="px-4 py-3">Outs</th>
                                           <th className="px-4 py-3">Strike Rate</th>
                                           <th className="px-4 py-3">Average</th>
                                       </tr>
                                   </thead>
                                   <tbody className="divide-y divide-gray-100">
                                       {battingStatsTeam2.map((p: any, i) => (
                                           <tr key={i} className="hover:bg-gray-50">
                                               <td className="px-4 py-2 font-medium text-gray-800">{p.name}</td>
                                               <td className="px-4 py-2 text-gray-700">{p.runs}</td>
                                               <td className="px-4 py-2 text-gray-700">{p.balls}</td>
                                               <td className="px-4 py-2 text-gray-700">{p.outs}</td>
                                               <td className="px-4 py-2 text-gray-700">{p.strike_rate.toFixed(2)}</td>
                                               <td className="px-4 py-2 text-gray-700">{p.outs > 0 ? (p.runs / p.outs).toFixed(2) : p.runs}</td>
                                           </tr>
                                       ))}
                                   </tbody>
                               </table>
                           </div>
                        </div>

                        {/* Cricket Runs per Over Comparison (Bar Chart) */}
                        <div className="mb-10 mt-6">
                            <h4 className="text-lg font-bold text-center text-gray-800 mb-6 uppercase tracking-wider">
                                📊 Runs per Over Comparison
                            </h4>
                            <div className="h-80 w-full p-4 bg-gray-50 rounded-lg border border-gray-200 shadow-sm mb-6">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={cricketPerOverData} margin={{ top: 20, right: 30, left: 10, bottom: 10 }}>
                                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                                        <XAxis dataKey="name" tick={{fontSize: 12, fill: '#6B7280'}} tickMargin={10} axisLine={{stroke: '#D1D5DB'}} />
                                        <YAxis tick={{fontSize: 12, fill: '#6B7280'}} tickMargin={10} axisLine={false} tickLine={false} />
                                        <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #E5E7EB', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }} cursor={{fill: '#F3F4F6'}} />
                                        <Legend iconType="circle" wrapperStyle={{ paddingTop: '10px' }} />
                                        <Bar dataKey={getTeamName(activeMatch.team1_id)} fill="#3b82f6" radius={[4, 4, 0, 0]} barSize={20} />
                                        <Bar dataKey={getTeamName(activeMatch.team2_id)} fill="#f97316" radius={[4, 4, 0, 0]} barSize={20} />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </div>
                )}
                
                {/* Generic / Non-Cricket Specific Blocks (Table tennis/kabaddi/bball quarters) */}
                {sport !== 'cricket' && quarterData.length > 0 && (
                   <div className="mb-10">
                       <h4 className="text-lg font-bold text-center text-gray-800 mb-6 uppercase tracking-wider">
                           {sport === 'table_tennis' ? 'Set-by-Set Score Comparison' : 'Period Analysis Comparison'}
                       </h4>
                       <div className="h-80 w-full p-4 bg-gray-50 rounded-lg border border-gray-200 shadow-sm mb-6">
                           <ResponsiveContainer width="100%" height="100%">
                               <BarChart data={quarterData} margin={{ top: 20, right: 30, left: 10, bottom: 10 }}>
                                   <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                                   <XAxis dataKey="name" tick={{fontSize: 12, fill: '#6B7280'}} tickMargin={10} axisLine={{stroke: '#D1D5DB'}} />
                                   <YAxis tick={{fontSize: 12, fill: '#6B7280'}} tickMargin={10} axisLine={false} tickLine={false} />
                                   <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #E5E7EB', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }} cursor={{fill: '#F3F4F6'}} />
                                   <Legend iconType="circle" wrapperStyle={{ paddingTop: '10px' }} />
                                   <Bar dataKey={getTeamName(activeMatch.team1_id)} fill="#3b82f6" radius={[4, 4, 0, 0]} barSize={40} />
                                   <Bar dataKey={getTeamName(activeMatch.team2_id)} fill="#22c55e" radius={[4, 4, 0, 0]} barSize={40} />
                               </BarChart>
                           </ResponsiveContainer>
                       </div>
                   </div>
                )}
                
                {kabaddiStats && sport === 'kabaddi' && (
                    <div className="bg-orange-50 border border-orange-200 rounded-lg p-6 mb-10 shadow-sm animate-fade-in">
                        <h4 className="text-xl font-bold text-orange-900 mb-6 flex items-center gap-2">🤼 Kabaddi Match Performance</h4>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                             <div className="bg-white p-4 rounded border border-orange-100 shadow-sm text-center">
                                 <div className="text-xs text-gray-500 uppercase font-bold tracking-wider mb-1">Total Raids</div>
                                 <div className="text-2xl font-black text-gray-800">{kabaddiStats.totalRaids}</div>
                                 <div className="text-xs text-gray-400 mt-1">{kabaddiStats.emptyRaids} Empty</div>
                             </div>
                             <div className="bg-white p-4 rounded border border-orange-100 shadow-sm text-center">
                                 <div className="text-xs text-gray-500 uppercase font-bold tracking-wider mb-1">Successful Raids</div>
                                 <div className="text-2xl font-black text-green-600">{kabaddiStats.successfulRaids}</div>
                                 <div className="text-xs text-orange-500 font-bold mt-1">{kabaddiStats.raidSuccess}% Rate</div>
                             </div>
                             <div className="bg-white p-4 rounded border border-orange-100 shadow-sm text-center">
                                 <div className="text-xs text-gray-500 uppercase font-bold tracking-wider mb-1">Tackle Points</div>
                                 <div className="text-2xl font-black text-blue-600">{kabaddiStats.tacklePoints}</div>
                                 <div className="text-xs text-gray-400 mt-1">{kabaddiStats.totalTackles} Total Tackles</div>
                             </div>
                             <div className="bg-white p-4 rounded border border-orange-100 shadow-sm text-center">
                                 <div className="text-xs text-gray-500 uppercase font-bold tracking-wider mb-1">Tackle Success</div>
                                 <div className="text-2xl font-black text-purple-600">{kabaddiStats.successfulTackles}</div>
                                 <div className="text-xs text-purple-500 font-bold mt-1">{kabaddiStats.tackleSuccess}% Rate</div>
                             </div>
                        </div>
                    </div>
                )}

                <h4 className="text-lg font-bold text-center text-gray-800 mb-6 uppercase tracking-wider">📈 Cumulative Match Flow</h4>
                <div className="h-96 w-full p-4 bg-gray-50 rounded-lg border border-gray-200 shadow-inner mb-10">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData} margin={{ top: 20, right: 30, left: 10, bottom: 10 }}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                            <XAxis 
                                dataKey="name" 
                                tick={{fontSize: 12, fill: '#6B7280'}} 
                                tickMargin={10} 
                                axisLine={{stroke: '#D1D5DB'}}
                            />
                            <YAxis 
                                tick={{fontSize: 12, fill: '#6B7280'}} 
                                tickMargin={10} 
                                axisLine={false} 
                                tickLine={false}
                            />
                            <Tooltip 
                                contentStyle={{ borderRadius: '8px', border: '1px solid #E5E7EB', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                            />
                            <Legend iconType="circle" wrapperStyle={{ paddingTop: '20px' }} />
                            <Line 
                                type="monotone" 
                                dataKey={getTeamName(activeMatch.team1_id)} 
                                stroke="#3b82f6" 
                                strokeWidth={3}
                                dot={false} 
                                activeDot={{ r: 6, strokeWidth: 0 }} 
                                animationDuration={1000}
                            />
                            <Line 
                                type="monotone" 
                                dataKey={getTeamName(activeMatch.team2_id)} 
                                stroke={sport === 'cricket' ? '#f97316' : '#22c55e'} 
                                strokeWidth={3}
                                dot={false} 
                                activeDot={{ r: 6, strokeWidth: 0 }} 
                                animationDuration={1000}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>

                {/* Match Awards (Cricket only) */}
                {sport === 'cricket' && (
                    <div className="mb-6">
                       <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">🏆 Match Awards</h3>
                       
                       {bestPlayer && (
                           <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg mb-4 text-yellow-800 shadow-sm">
                               <span className="font-bold">🥇 Best Player:</span> <span className="font-extrabold">{bestPlayer.name}</span> — 
                               MVP Score: {bestPlayer.mvp_score.toFixed(1)}, Runs: {bestPlayer.runs}, Wickets: {bestPlayer.wickets}
                           </div>
                       )}

                       {bestBowler && (
                           <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg mb-6 text-blue-800 shadow-sm">
                               <span className="font-bold">🎯 Best Bowler:</span> <span className="font-extrabold">{bestBowler.name}</span> — 
                               {bestBowler.wickets} wickets, Econ {bestBowler.economy.toFixed(2)}
                           </div>
                       )}

                       <h4 className="font-bold text-gray-700 mt-6 mb-2 flex items-center gap-2">🌟 Star Performers – Top 3</h4>
                       <div className="bg-white border border-gray-200 rounded overflow-hidden shadow-sm">
                           <table className="w-full text-sm text-left">
                               <thead className="bg-gray-50 text-gray-600 border-b border-gray-200">
                                   <tr>
                                       <th className="px-4 py-3">Player Name</th>
                                       <th className="px-4 py-3">Runs</th>
                                       <th className="px-4 py-3">Wickets</th>
                                       <th className="px-4 py-3">Catches</th>
                                       <th className="px-4 py-3">Strike Rate</th>
                                       <th className="px-4 py-3">Economy</th>
                                       <th className="px-4 py-3">MVP Score</th>
                                   </tr>
                               </thead>
                               <tbody className="divide-y divide-gray-100">
                                   {top3Performers.map((p: any, i: number) => (
                                       <tr key={i} className="hover:bg-gray-50">
                                           <td className="px-4 py-2 font-medium text-gray-800">{p.name}</td>
                                           <td className="px-4 py-2 text-gray-700">{p.runs}</td>
                                           <td className="px-4 py-2 text-gray-700">{p.wickets}</td>
                                           <td className="px-4 py-2 text-gray-700">{p.catches}</td>
                                           <td className="px-4 py-2 text-gray-700">{p.strike_rate.toFixed(1)}</td>
                                           <td className="px-4 py-2 text-gray-700">{p.economy.toFixed(2)}</td>
                                           <td className="px-4 py-2 text-gray-700 font-semibold">{p.mvp_score.toFixed(1)}</td>
                                       </tr>
                                   ))}
                               </tbody>
                           </table>
                       </div>
                    </div>
                )}
            </div>
        ) : mid ? (
             <div className="text-gray-500 italic text-center py-10 bg-gray-50 rounded border border-gray-200">
                 No scores found for this match to plot.
             </div>
        ) : (
             <div className="text-gray-500 font-medium text-center py-12 bg-gray-50 rounded-lg border border-gray-200 shadow-inner">
                 Select a tournament and match to view performance graphs.
             </div>
        )}
      </div>

      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <h3 className="text-xl font-bold mb-6 text-gray-800 border-b border-gray-200 pb-3 flex items-center gap-2">🌐 Global {sport?.replace('_', ' ')} Overview</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-4">
          <div className="bg-blue-50 p-6 rounded-xl border border-blue-100 flex flex-col justify-center items-center shadow-sm">
              <h4 className="text-blue-600 font-bold uppercase text-xs tracking-wider mb-2">Total Matches</h4>
              <span className="text-5xl font-extrabold text-blue-800">{stats.matches?.length || 0}</span>
          </div>
          <div className="bg-green-50 p-6 rounded-xl border border-green-100 flex flex-col justify-center items-center shadow-sm">
              <h4 className="text-green-600 font-bold uppercase text-xs tracking-wider mb-2">Teams Registered</h4>
              <span className="text-5xl font-extrabold text-green-800">{stats.teams?.length || 0}</span>
          </div>
          <div className="bg-purple-50 p-6 rounded-xl border border-purple-100 flex flex-col justify-center items-center shadow-sm">
              <h4 className="text-purple-600 font-bold uppercase text-xs tracking-wider mb-2">Total Players</h4>
              <span className="text-5xl font-extrabold text-purple-800">{stats.players?.length || 0}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
"""

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated React Stats Component with Light Theme and Bar Chart")
