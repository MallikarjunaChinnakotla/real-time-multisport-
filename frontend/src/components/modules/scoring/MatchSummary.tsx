import React from 'react';

export default function MatchSummary({ 
    sport, 
    winnerName, 
    winMargin, 
    bestPlayers // Array of objects: { title: 'Player of the Match', name: 'John Doe', stat: '50 runs' }
}: {
    sport: string,
    winnerName: string,
    winMargin: string,
    bestPlayers: {title: string, name: string, stat: string}[]
}) {
    return (
        <div className="bg-gradient-to-br from-blue-900 to-indigo-800 rounded-2xl p-8 text-gray-900 shadow-2xl relative overflow-hidden animate-fade-in text-center mt-8">
            <div className="absolute top-0 right-0 p-4 opacity-10 text-9xl">🏆</div>
            <h2 className="text-4xl font-black mb-2 tracking-tight">MATCH FINISHED</h2>
            <div className="h-1 w-24 bg-yellow-400 mx-auto mb-8 rounded-full"></div>

            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-8 mb-8 border border-white/20">
                <div className="text-yellow-400 text-sm font-bold tracking-widest uppercase mb-1">Winner</div>
                <div className="text-5xl font-black mb-3 drop-shadow-md">{winnerName}</div>
                <div className="text-xl text-blue-200 font-medium">Won by {winMargin}</div>
            </div>

            <h3 className="text-2xl font-bold mb-6 text-blue-100 border-b border-white/20 pb-3 inline-block px-8">Award Winners</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {bestPlayers.map((bp, i) => (
                    <div key={i} className="bg-white/5 border border-white/10 rounded-xl p-6 hover:bg-white/10 transition flex flex-col items-center">
                        <div className="text-3xl mb-3">{i === 0 ? '🎖️' : '🏅'}</div>
                        <div className="text-sm text-blue-300 font-bold uppercase tracking-wider mb-2">{bp.title}</div>
                        <div className="text-xl font-bold text-gray-900 mb-1">{bp.name}</div>
                        <div className="text-md text-yellow-300 font-medium">{bp.stat}</div>
                    </div>
                ))}
            </div>
            
            <div className="mt-10 mb-2">
                <button className="bg-white text-indigo-900 font-bold py-3 px-8 rounded-full shadow-lg hover:bg-gray-100 transition-transform hover:scale-105" onClick={() => window.location.reload()}>
                    Back to Matches
                </button>
            </div>
        </div>
    );
}
