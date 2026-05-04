# Ultimate Air Hockey

A feature-rich air hockey game built with Python and Pygame.

## Features

- **Two game modes:** Two Players (local) or Player vs AI
- **AI difficulty levels:** Easy, Medium, Hard
- **Power-ups:** Speed boost, Big paddle, Slow opponent
- **Particle effects** on goals
- **Screen shake** on collisions
- **Puck trail** and spin physics
- **Animated rink** with glowing center circle

## Controls

### Player 1 (Blue)
| Action | Key |
|--------|-----|
| Move Up | W |
| Move Down | S |
| Move Left | A |
| Move Right | D |

### Player 2 (Red) — Two Player mode only
| Action | Key |
|--------|-----|
| Move Up | ↑ |
| Move Down | ↓ |
| Move Left | ← |
| Move Right | → |

### General
| Action | Key |
|--------|-----|
| Pause | P |
| Restart (while paused) | R |
| Menu (while paused) | M |

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the game:
   ```bash
   python air_hockey.py
   ```

## Rules

- First to **7 goals** wins.
- Power-ups spawn every 10 seconds in the center of the rink.
- Each player is restricted to their own half of the rink.
