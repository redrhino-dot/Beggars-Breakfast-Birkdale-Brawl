import json, urllib.request, datetime, re

with open('teams.json') as f:
    TEAMS = json.load(f)

ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/golf/leaderboard?league=pga"

def fetch():
    req = urllib.request.Request(ESPN_URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)

def parse_position(pos_str):
    """Turn 'T5', '1', '-' into an integer position. Returns None if not yet set."""
    if not pos_str or pos_str == '-':
        return None
    m = re.search(r'\d+', pos_str)
    return int(m.group()) if m else None

def build():
    raw = fetch()
    event = raw['events'][0]
    comp = event['competitions'][0]

    players = {}
    made_cut_positions = []

    # First pass: collect raw position/status per player
    for c in comp['competitors']:
        name = c['athlete']['displayName']
        status_desc = c.get('status', {}).get('type', {}).get('description', '') or ''
        pos_display = c.get('status', {}).get('position', {}).get('displayName', '-')
        score_val = c.get('score', {}).get('displayValue', 'E')
        is_cut = 'cut' in status_desc.lower() or 'wd' in status_desc.lower()

        pos_num = parse_position(pos_display)
        players[name] = {
            'score': score_val,
            'position_display': pos_display,
            'status': status_desc,
            'is_cut': is_cut,
            'pos_num': pos_num
        }
        if not is_cut and pos_num is not None:
            made_cut_positions.append(pos_num)

    # Determine cut line: worst position among players who made the cut
    cut_line = max(made_cut_positions) if made_cut_positions else None
    cut_line_plus_one = (cut_line + 1) if cut_line is not None else 999

    # Second pass: assign final scoring position
    for name, info in players.items():
        if info['is_cut']:
            info['scoring_position'] = cut_line_plus_one
            info['position_display'] = f"CUT ({cut_line_plus_one})"
        elif info['pos_num'] is not None:
            info['scoring_position'] = info['pos_num']
        else:
            # Not started / no position yet — treat as last + 1 for now
            info['scoring_position'] = cut_line_plus_one
            info['position_display'] = 'Not Started'

    teams_out = []
    for team, roster in TEAMS.items():
        members = []
        total = 0
        for p in roster:
            info = players.get(p, {
                'score': '-', 'position_display': 'Not Started',
                'status': 'Not Started', 'scoring_position': cut_line_plus_one
            })
            members.append({
                'name': p,
                'score': info['score'],
                'position': info['position_display'],
                'status': info['status'],
                'scoringPosition': info['scoring_position']
            })
            total += info['scoring_position']
        teams_out.append({'team': team, 'total': total, 'players': members})

    teams_out.sort(key=lambda t: t['total'])
    for i, t in enumerate(teams_out, 1):
        t['rank'] = i

    output = {
        'lastUpdated': datetime.datetime.utcnow().isoformat() + 'Z',
        'tournament': event.get('name', 'The Open Championship — Royal Birkdale'),
        'cutLine': cut_line,
        'teams': teams_out
    }

    with open('data.json', 'w') as f:
        json.dump(output, f, indent=2)

if __name__ == '__main__':
    build()
