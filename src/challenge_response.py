import random

CHALLENGES = [
    {"type": "blink", "instruction": "Please blink your eyes twice"},
    {"type": "turn_head_left", "instruction": "Turn your head to the left"},
    {"type": "turn_head_right", "instruction": "Turn your head to the right"},
    {"type": "smile", "instruction": "Please smile"},
    {"type": "open_mouth", "instruction": "Open your mouth"},
]

def get_random_challenge():
    return random.choice(CHALLENGES)
