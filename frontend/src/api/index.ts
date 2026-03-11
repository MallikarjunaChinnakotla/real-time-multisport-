import axios from "axios";

// If using vite + local dev server on different port, point to backend.
const api = axios.create({
    baseURL: "http://localhost:8000/api",
});

export const getTournaments = (sport: string) => api.get(`/${sport}/tournaments`);
export const addTournament = (sport: string, data: any) => api.post(`/${sport}/tournaments`, data);
export const deleteTournament = (sport: string, id: number) => api.delete(`/${sport}/tournaments/${id}`);

export const getTeams = (sport: string) => api.get(`/${sport}/teams`);
export const addTeam = (sport: string, data: any) => api.post(`/${sport}/teams`, data);
export const deleteTeam = (sport: string, id: number) => api.delete(`/${sport}/teams/${id}`);

export const getPlayers = (sport: string) => api.get(`/${sport}/players`);
export const addPlayer = (sport: string, data: any) => api.post(`/${sport}/players`, data);
export const deletePlayer = (sport: string, id: number) => api.delete(`/${sport}/players/${id}`);

export const getMatches = (sport: string) => api.get(`/${sport}/matches`);
export const addMatch = (sport: string, data: any) => api.post(`/${sport}/matches`, data);
export const deleteMatch = (sport: string, id: number) => api.delete(`/${sport}/matches/${id}`);

export const getScores = (sport: string, matchId?: number) => {
    let url = `/${sport}/scores`;
    if (matchId !== undefined) {
        url += `?match_id=${matchId}`;
    }
    return api.get(url);
};
export const addScore = (sport: string, data: any) => api.post(`/${sport}/scores`, data);

export const getStats = (sport: string) => api.get(`/${sport}/stats`);

export default api;
