import React from 'react';
import { useParams } from 'react-router-dom';
import * as ScoringModules from './scoring';

const LiveScoring = () => {
  const { sport } = useParams<{ sport: string }>();

  const componentMap: Record<string, React.FC> = {
    cricket: ScoringModules.CricketScoring,
    football: ScoringModules.FootballScoring,
    basketball: ScoringModules.BasketballScoring,
    volleyball: ScoringModules.VolleyballScoring,
    kabaddi: ScoringModules.KabaddiScoring,
    handball: ScoringModules.HandballScoring,
    table_tennis: ScoringModules.TableTennisScoring,
    hockey: ScoringModules.HockeyScoring,
    softball: ScoringModules.SoftballScoring
  };

  const SelectedModule = sport ? componentMap[sport] : null;

  if (SelectedModule) {
      return (
          <div className="bg-white text-gray-900 min-h-[calc(100vh-8rem)] rounded-xl overflow-hidden shadow">
              <SelectedModule />
          </div>
      );
  }

  return <div className="p-8 text-center text-gray-500">Live Scoring coming soon for this sport!</div>;
};

export default LiveScoring;
