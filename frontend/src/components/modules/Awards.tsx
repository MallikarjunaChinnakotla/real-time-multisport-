import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import * as api from '../../api';

const Awards = () => {
  const { sport } = useParams<{ sport: string }>();
  const [stats, setStats] = useState<any>(null);
  const [tid, setTid] = useState<string>('');

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
      <div className="space-y-6">
          <div className="bg-gradient-to-br from-yellow-500 to-amber-600 p-8 rounded-xl shadow-lg border border-yellow-600 text-white flex flex-col md:flex-row items-center animate-pulse">
              <div className="md:w-1/3 flex justify-center pb-6 md:pb-0">
                  <div className="bg-white/20 w-32 h-32 rounded-full"></div>
              </div>
              <div className="md:w-2/3 md:pl-8 text-center md:text-left h-24">
                   <div className="h-6 w-48 bg-white/30 mb-4 rounded mx-auto md:mx-0"></div>
                   <div className="h-10 w-64 bg-white/40 mb-3 drop-shadow-md rounded mx-auto md:mx-0"></div>
              </div>
          </div>
      </div>
  );

  const activeTournaments = stats.tournaments || [];

  const getFilteredScores = () => {
      if (!stats || !tid) return [];
      const matchIdsInTournament = new Set(
          stats.matches
              ?.filter((m: any) => m.tournament_id == tid)
              .map((m: any) => m.match_id)
      );
      return stats.scores?.filter((s: any) => matchIdsInTournament.has(s.match_id)) || [];
  };

  const filteredScores = getFilteredScores();

  // Basic aggregation logic dynamically pulling from CSV data keys
  const getTopPlayer = () => {
      if (!tid) return null;
      const pCounts: Record<string, number> = {};
      filteredScores.forEach((s: any) => {
           let val = s.runs || s.points || 1;
           let name = s.striker || s.player_name || s.player || s.player_id;
           // If ID is returned, try to map it using stats.players
           const pInfo = stats.players?.find((p:any) => p.player_id == name);
           if (pInfo) name = pInfo.player_name;
           
           if (name) {
               pCounts[name] = (pCounts[name] || 0) + Number(val);
           }
      });
      const entries = Object.entries(pCounts);
      if (!entries.length) return null;
      entries.sort((a, b) => b[1] - a[1]);
      return entries[0];
  };

  const mvp = getTopPlayer();

  return (
    <div className="space-y-6">
      
      {/* Tournament Selection Header */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 animate-fade-in">
          <h2 className="text-xl font-bold mb-4 text-gray-800 flex items-center gap-2">🏆 Select Tournament for Awards</h2>
          <select 
              className="w-full md:w-1/2 border border-gray-300 rounded shadow-sm py-2 px-3 text-gray-800 outline-none focus:ring-2 focus:ring-yellow-500 bg-white" 
              value={tid} 
              onChange={e => setTid(e.target.value)}
          >
              <option value="">-- Choose a Tournament --</option>
              {activeTournaments.map((t: any, i: number) => (
                  <option key={i} value={t?.tournament_id || t}>
                      {t?.tournament_name ? `Tournament: ${t.tournament_name}` : `Tournament #${t?.tournament_id || t}`}
                  </option>
              ))}
          </select>
          {!tid && <p className="text-red-500 text-sm mt-3 italic">⚠️ You must select a tournament to view its awards and statistics.</p>}
      </div>

      {!tid ? (
          <div className="text-center text-gray-400 py-10 bg-gray-50 border border-gray-200 rounded-lg">
              <span className="text-4xl mb-3 block">🏅</span> Please select a tournament from the dropdown above to load the summary.
          </div>
      ) : (
      <>
        <div className="bg-gradient-to-br from-yellow-500 to-amber-600 p-8 rounded-xl shadow-lg border border-yellow-600 text-white flex flex-col md:flex-row items-center animate-fade-in">
        <div className="md:w-1/3 flex justify-center pb-6 md:pb-0">
            <div className="bg-white/20 p-6 rounded-full backdrop-blur-sm border border-white/30 shadow-2xl">
                 <svg className="w-24 h-24 text-yellow-100" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 2a1 1 0 011 1v1.323l3.954 1.582 1.599-.8a1 1 0 01.894 1.79l-1.233.616 1.738 5.42a1 1 0 01-.285 1.05A3.989 3.989 0 0115 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.715-5.349L11 6.477V16h2a1 1 0 110 2H7a1 1 0 110-2h2V6.477L6.237 7.582l1.715 5.349a1 1 0 01-.285 1.05A3.989 3.989 0 015 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.738-5.42-1.233-.617a1 1 0 01.894-1.788l1.599.799L9 4.323V3a1 1 0 011-1z" clipRule="evenodd"></path></svg>
            </div>
        </div>
        <div className="md:w-2/3 md:pl-8 text-center md:text-left">
            <h2 className="text-sm uppercase tracking-widest font-bold text-amber-100 mb-2">Tournament Most Valuable Player (MVP)</h2>
            {mvp ? (
                <>
                   <h1 className="text-4xl md:text-5xl font-extrabold mb-3 drop-shadow-md">{mvp[0]}</h1>
                   <p className="text-xl text-yellow-50 bg-black/10 inline-block px-4 py-2 rounded-full font-semibold backdrop-blur-sm border border-white/10">
                       Top Actions / Points Generated: <span className="text-white">{mvp[1]}</span>
                   </p>
                </>
            ) : (
                <div className="text-2xl font-semibold italic text-amber-200">Awaiting score results to determine MVP...</div>
            )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <h3 className="text-lg font-semibold mb-4 text-gray-800 border-b pb-2">Top Performers / Leaderboard</h3>
              {mvp ? (
                  <ul className="space-y-3">
                      {(() => {
                          const pCounts: Record<string, number> = {};
                          filteredScores.forEach((s: any) => {
                               let val = s.runs || s.points || 1;
                               let name = s.striker || s.player_name || s.player || s.player_id;
                               const pInfo = stats.players?.find((p:any) => p.player_id == name);
                               if (pInfo) name = pInfo.player_name;
                               if (name) pCounts[name] = (pCounts[name] || 0) + Number(val);
                          });
                          let entries = Object.entries(pCounts).sort((a, b) => b[1] - a[1]).slice(0, 10);
                          if(entries.length === 0) {
                              return <div className="text-gray-500 italic text-center py-8">No action points detected.</div>;
                          }
                          return entries.map((en, i) => (
                               <li key={i} className={`flex justify-between items-center p-3 rounded border ${i===0 ? 'bg-yellow-50 border-yellow-200' : 'bg-gray-50 border-gray-100'}`}>
                                   <div className="flex items-center">
                                       <span className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm mr-3 ${i===0 ? 'bg-yellow-400 text-yellow-900' : i===1 ? 'bg-gray-300 text-gray-800' : i===2 ? 'bg-amber-600 text-white' : 'bg-gray-200 text-gray-600'}`}>{i+1}</span>
                                       <span className="font-medium text-gray-800">{en[0]}</span>
                                   </div>
                                   <span className="font-bold text-blue-600 bg-blue-100 px-3 py-1 rounded-full text-sm">{en[1]} Pts</span>
                               </li>
                          ));
                      })()}
                  </ul>
              ) : (
                  <div className="text-gray-500 italic text-center py-8">Generate more events to populate the leaderboard.</div>
              )}
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 flex flex-col items-center justify-center text-center">
              <div className="bg-blue-100 p-6 rounded-full mb-6">
                  <svg className="w-16 h-16 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
              </div>
              <h3 className="text-xl font-bold text-gray-800 mb-2">Machine Learning Summary</h3>
              <p className="text-gray-600 mb-6 max-w-sm">Models such as win_predictor.pkl or score_predictor.pkl processes aggregate CSV endpoints automatically.</p>
              <button disabled className="bg-gray-300 text-gray-500 font-semibold px-6 py-3 rounded-lg shadow-inner cursor-not-allowed">Auto-Syncing enabled with APIs</button>
          </div>
      </div>
      </>
      )}
    </div>
  );
};
export default Awards;
