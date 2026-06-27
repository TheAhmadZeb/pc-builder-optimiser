const gameSelect = document.getElementById('game-select');
const poster = document.getElementById('game-poster') || document.querySelector('.feature-poster');

const GAME_POSTERS = {
  'FORTNITE': 'fortnite.png',
  'MINECRAFT': 'minecraft.png',
  'WOLFENSTEIN II: THE NEW COLOSSUS': 'wolfenstein_ii_the_new_colossus.png',
  'VALORANT': 'valorant.png',
  'RAINBOW SIX SIEGE': 'rainbow_six_siege.png',
  'CS:GO': 'csgo.png',
  'CYBERPUNK 2077': 'cyberpunk_2077.png',
  'CALL OF DUTY WARZONE': 'call_of_duty_warzone.png',
  'GTA V': 'gta_v.png',
  'RED DEAD REDEMPTION 2': 'red_dead_redemption_2.png',
  'APEX LEGENDS': 'apex_legends.png',
  'ELDEN RING': 'elden_ring.png',
  'STARFIELD': 'starfield.png',
  'FORZA HORIZON 5': 'forza_horizon_5.png',
  'THE WITCHER 3': 'the_witcher_3.png'
};

function normaliseGameTitle(title) {
  return title.trim().replace(/\s+/g, ' ').toUpperCase();
}

function updateGamePoster() {
  if (!gameSelect || !poster) return;
  const selectedTitle = normaliseGameTitle(gameSelect.options[gameSelect.selectedIndex].text);
  const imageBase = poster.dataset.gameImageBase || '/static/assets/games/';
  const posterFile = GAME_POSTERS[selectedTitle] || 'fortnite.png';
  poster.src = imageBase + posterFile;
  poster.alt = `${selectedTitle} poster`;
}

if (gameSelect && poster) {
  gameSelect.addEventListener('change', updateGamePoster);
  updateGamePoster();
}
