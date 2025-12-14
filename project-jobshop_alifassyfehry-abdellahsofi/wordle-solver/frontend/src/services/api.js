import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const wordleApi = {
  // Obtenir les langues disponibles
  getLanguages: async () => {
    const response = await api.get('/languages');
    return response.data;
  },

  // Obtenir les stratégies disponibles
  getStrategies: async () => {
    const response = await api.get('/strategies');
    return response.data;
  },

  // Créer une nouvelle partie
  newGame: async (language = 'en', strategy = 'frequency', targetWord = null) => {
    const response = await api.post('/game/new', {
      language,
      strategy,
      target_word: targetWord,
    });
    return response.data;
  },

  // Faire une tentative
  makeGuess: async (gameId, guess) => {
    const response = await api.post('/game/guess', {
      game_id: gameId,
      guess,
    });
    return response.data;
  },

  // Obtenir des suggestions
  getSuggestions: async (gameId, limit = 10) => {
    const response = await api.post('/game/suggest', {
      game_id: gameId,
      limit,
    });
    return response.data;
  },

  // Obtenir l'état d'une partie
  getGameState: async (gameId) => {
    const response = await api.get(`/game/state/${gameId}`);
    return response.data;
  },

  // Supprimer une partie
  deleteGame: async (gameId) => {
    const response = await api.delete(`/game/${gameId}`);
    return response.data;
  },

  // Obtenir les statistiques
  getStats: async () => {
    const response = await api.get('/stats');
    return response.data;
  },

  // Obtenir la définition d'un mot via Gemini
  getWordDefinition: async (word, language = 'fr') => {
    const response = await api.post('/word/definition', {
      word,
      language,
    });
    return response.data;
  },
};

export default wordleApi;
