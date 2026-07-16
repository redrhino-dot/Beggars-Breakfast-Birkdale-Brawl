async function loadLeaderboard() {
  const res = await fetch('data.json', { cache: 'no-store' });
  const data = await res.json();

  document.getElementById('tournamentName').textContent = data.tournament;
  document.getElementById('lastUpdated').textContent =
    'Last updated: ' + new Date(data.lastUpdated).toLocaleString('en-GB', { timeZone: 'Europe/London' }) +
    (data.cutLine ? ` | Cut line: T${data.cutLine}` : '');

  const board = document.getElementById('leaderboard');
  board.innerHTML = '';

  data.teams.forEach(team => {
    const card = document.createElement('div');
    card.className = 'team-card';

    card.innerHTML = `
      <div class="team-header">
        <span class="rank">${team.rank}</span>
        <span class="team-name">${team.team}</span>
        <span class="team-total">${team.total} pts</span>
      </div>
      <div class="players">
        ${team.players.map(p => `
          <div class="player-row">
            <span>${p.name}</span>
            <span>${p.position} (${p.score}) — ${p.scoringPosition}</span>
          </div>
        `).join('')}
      </div>
    `;

    card.querySelector('.team-header').addEventListener('click', () => {
      card.querySelector('.players').classList.toggle('open');
    });

    board.appendChild(card);
  });
}

loadLeaderboard();
setInterval(loadLeaderboard, 60000);
