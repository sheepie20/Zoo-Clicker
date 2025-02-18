from flask import Flask, render_template, jsonify, request, session, redirect
from datetime import datetime
import random
from collections import OrderedDict

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for session management

# Game configuration
ANIMALS = OrderedDict([
    ('Mice', {'base_cost': 10, 'income': 0.1, 'image': '/static/images/mice.jpg'}),
    ('Hamster', {'base_cost': 50, 'income': 0.5, 'image': '/static/images/hamster.jpg'}),
    ('Guinea Pig', {'base_cost': 100, 'income': 1, 'image': '/static/images/guinea_pig.jpg'}),
    ('Ferret', {'base_cost': 500, 'income': 5, 'image': '/static/images/ferret.jpg'}),
    ('Rabbit', {'base_cost': 1000, 'income': 10, 'image': '/static/images/rabbit.jpg'}),
    ('Lizard', {'base_cost': 5000, 'income': 50, 'image': '/static/images/lizard.jpg'}),
    ('Blue Jay', {'base_cost': 10000, 'income': 100, 'image': '/static/images/blue_jay.jpg'}),
    ('Parrot', {'base_cost': 50000, 'income': 500, 'image': '/static/images/parrot.jpg'}),
    ('Fox', {'base_cost': 100000, 'income': 1000, 'image': '/static/images/fox.jpg'}),
    ('Tarantulas', {'base_cost': 500000, 'income': 5000, 'image': '/static/images/tarantula.jpg'}),
    ('Garden Snake', {'base_cost': 1000000, 'income': 10000, 'image': '/static/images/garden_snake.jpg'}),
    ('Wolf', {'base_cost': 5000000, 'income': 50000, 'image': '/static/images/wolf.jpg'})
])

IMPROVEMENTS = OrderedDict([
    ('Security', {'cost': 1000, 'multiplier': 1.5}),
    ('Zookeeper', {'cost': 5000, 'multiplier': 2}),
    ('Manager', {'cost': 25000, 'multiplier': 3}),
    ('Australian', {'cost': 100000, 'multiplier': 5})
])

EVENTS = {
    'Infestation': {
        'Termites': {
            'chance': 0.02, 'penalty': 0.9,
            'solution': {'type': 'clicks', 'amount': 50, 'description': 'Click 50 times to spray pesticide'}
        },
        'Rat': {
            'chance': 0.015, 'penalty': 0.8,
            'solution': {'type': 'clicks', 'amount': 100, 'description': 'Click 100 times to set traps'}
        },
        'Hornets': {
            'chance': 0.01, 'penalty': 0.7,
            'solution': {'type': 'coins', 'amount': 1000, 'description': 'Pay 1,000 coins for pest control'}
        },
        'Cane Toads': {
            'chance': 0.008, 'penalty': 0.6,
            'solution': {'type': 'coins', 'amount': 5000, 'description': 'Pay 5,000 coins for toad removal'}
        },
        'Zombies': {
            'chance': 0.005, 'penalty': 0.5,
            'solution': {'type': 'coins', 'amount': 10000, 'description': 'Pay 10,000 coins for zombie cure'}
        }
    },
    'Holiday': {
        'Weekend': {'chance': 0.03, 'bonus': 1.5, 'duration': 60},  # 1 minute
        'Spring Break': {'chance': 0.02, 'bonus': 2, 'duration': 120},  # 2 minutes
        'Winter Break': {'chance': 0.01, 'bonus': 3, 'duration': 180},  # 3 minutes
        'Summer Break': {'chance': 0.008, 'bonus': 5, 'duration': 300}  # 5 minutes
    }
}

def calculate_animal_cost(base_cost, owned):
    """Calculate the cost of the next animal based on how many are owned"""
    return int(base_cost * (1.15 ** owned))

def init_game_state():
    return {
        'coins': 0,
        'animals': {name: 0 for name in ANIMALS},
        'improvements': {name: 0 for name in IMPROVEMENTS},
        'income_per_second': 0,
        'multiplier': 1,
        'active_events': [],
        'event_progress': {},
        'dark_mode': False,
        'last_tick': datetime.now().timestamp()
    }

@app.route('/')
def home():
    return redirect('/game')

@app.route('/game')
def game():
    game_state = session.get('game_state', init_game_state())
    if 'dark_mode' not in game_state:
        game_state['dark_mode'] = False
    session['game_state'] = game_state
    return render_template('game.html', 
                         animals=ANIMALS, 
                         improvements=IMPROVEMENTS,
                         game_state=game_state)

@app.route('/api/toggle_theme', methods=['POST'])
def toggle_theme():
    game_state = session.get('game_state', init_game_state())
    if 'dark_mode' not in game_state:
        game_state['dark_mode'] = False
    game_state['dark_mode'] = not game_state['dark_mode']
    session['game_state'] = game_state
    return jsonify(game_state)

@app.route('/api/solve_event', methods=['POST'])
def solve_event():
    event_name = request.json['event']
    solution_type = request.json['type']
    
    game_state = session.get('game_state', init_game_state())
    
    # Find the event in active events
    event_data = None
    for event in game_state['active_events']:
        if event['name'] == event_name:
            event_data = event
            break
    
    if not event_data:
        return jsonify({'error': 'Event not found'}), 400
        
    if solution_type == 'coins':
        required_coins = EVENTS['Infestation'][event_name]['solution']['amount']
        if game_state['coins'] < required_coins:
            return jsonify({'error': 'Not enough coins'}), 400
        game_state['coins'] -= required_coins
        game_state['active_events'].remove(event_data)
    
    session['game_state'] = game_state
    return jsonify(game_state)

@app.route('/api/click_progress', methods=['POST'])
def click_progress():
    event_name = request.json['event']
    
    game_state = session.get('game_state', init_game_state())
    if event_name not in game_state['event_progress']:
        game_state['event_progress'][event_name] = 0
    
    game_state['event_progress'][event_name] += 1
    
    # Check if we've reached the required clicks
    for event in game_state['active_events']:
        if event['name'] == event_name:
            required_clicks = EVENTS['Infestation'][event_name]['solution']['amount']
            if game_state['event_progress'][event_name] >= required_clicks:
                game_state['active_events'].remove(event)
                del game_state['event_progress'][event_name]
            break
    
    session['game_state'] = game_state
    return jsonify(game_state)

@app.route('/api/click', methods=['POST'])
def click():
    game_state = session.get('game_state', init_game_state())
    game_state['coins'] += 1 * game_state['multiplier']
    session['game_state'] = game_state
    return jsonify(game_state)

@app.route('/api/buy_animal', methods=['POST'])
def buy_animal():
    animal = request.json['animal']
    if animal not in ANIMALS:
        return jsonify({'error': 'Invalid animal'}), 400
    
    game_state = session.get('game_state', init_game_state())
    current_owned = game_state['animals'][animal]
    cost = calculate_animal_cost(ANIMALS[animal]['base_cost'], current_owned)
    
    if game_state['coins'] < cost:
        return jsonify({'error': 'Not enough coins'}), 400
    
    game_state['coins'] -= cost
    game_state['animals'][animal] += 1
    game_state['income_per_second'] = calculate_income(game_state)
    session['game_state'] = game_state
    
    return jsonify(game_state)

@app.route('/api/buy_improvement', methods=['POST'])
def buy_improvement():
    improvement = request.json['improvement']
    if improvement not in IMPROVEMENTS:
        return jsonify({'error': 'Invalid improvement'}), 400
    
    game_state = session.get('game_state', init_game_state())
    cost = IMPROVEMENTS[improvement]['cost']
    
    if game_state['coins'] < cost:
        return jsonify({'error': 'Not enough coins'}), 400
    
    game_state['coins'] -= cost
    game_state['improvements'][improvement] += 1
    game_state['multiplier'] = calculate_multiplier(game_state)
    session['game_state'] = game_state
    
    return jsonify(game_state)

@app.route('/api/tick', methods=['POST'])
def tick():
    game_state = session.get('game_state', init_game_state())
    
    # Process events
    process_events(game_state)
    
    # Add income
    income = game_state['income_per_second']
    for event in game_state['active_events']:
        if 'bonus' in event:
            income *= event['bonus']
        if 'penalty' in event:
            income *= event['penalty']
    
    game_state['coins'] += income
    session['game_state'] = game_state
    
    return jsonify(game_state)

def calculate_income(game_state):
    income = 0
    for animal, count in game_state['animals'].items():
        income += ANIMALS[animal]['income'] * count
    return income

def calculate_multiplier(game_state):
    multiplier = 1
    for improvement, count in game_state['improvements'].items():
        if count > 0:
            multiplier *= IMPROVEMENTS[improvement]['multiplier']
    return multiplier

def process_events(game_state):
    current_time = datetime.now().timestamp()
    last_tick = game_state.get('last_tick', current_time)
    game_state['last_tick'] = current_time
    
    # Remove expired holiday events
    game_state['active_events'] = [
        event for event in game_state['active_events']
        if event.get('type') == 'Infestation' or
           (event.get('start_time', current_time) + event.get('duration', 0) > current_time)
    ]
    
    # Only process new events if we don't have any active ones
    if not game_state['active_events']:
        # Check for new events
        for event_type, events in EVENTS.items():
            for name, data in events.items():
                if random.random() < data['chance']:
                    event_data = {
                        'type': event_type,
                        'name': name,
                        'start_time': current_time
                    }
                    if 'bonus' in data:
                        event_data['bonus'] = data['bonus']
                        event_data['duration'] = data['duration']
                    if 'penalty' in data:
                        event_data['penalty'] = data['penalty']
                        event_data['solution'] = data['solution']
                    game_state['active_events'].append(event_data)
                    break  # Only one event at a time

if __name__ == '__main__':
    app.run(debug=True)