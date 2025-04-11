# MystDoku

**MystDoku** is an original web-based game inspired by sudoku, combining logical puzzle-solving with a narrative adventure. The player unlocks the protagonist's memories and gradually uncovers their past.

## Contents
- [Game Overview](#game-overview)
- [Installation](#installation)
- [Running the Server](#running-the-server)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Technologies Used](#technologies-used)
- [Author](#author)

## Game Overview

> The game is divided into three difficulty levels. Each sudoku block is represented as a room filled with various items. Each item corresponds to a number from 1 to 9. After solving each game, a story sequence is unlocked and the game progresses.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Mitelin/MystDoku.git
cd MystDoku
```
2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
3. Install the dependencies:
```bash
pip install -r requirements.txt
```

## Running the Server

```bash
python manage.py migrate
python manage.py runserver
```

Then, load the fixture data manually:

```bash
python manage.py loaddata gameplay/fixtures/items.json
python manage.py loaddata gameplay/fixtures/story.json
python manage.py loaddata gameplay/fixtures/sequence_frames.json
```

The app will be available at `http://127.0.0.1:8000/`

### Key URLs

- Main page: `/`
- Game selection: `/game/selection/`
- Gameplay: `/game/<uuid:game_id>/`
- Scoreboard: `/score/`
- Story So Far: `/story/`
- API documentation: `/docs/api.md`

## Testing

To run tests using pytest:
```bash
pytest
```

## Project Structure

- `main/` – handles user registration, login, and player redirection
- `gameplay/` – game selection, gameplay flow, and story sequence playback
- `score/` – tracks player statistics and displays the scoreboard
- `static/` and `templates/` – styles and HTML templates
- `items.json` , `story_full.json` and `sequence_frames.json` – data for game items and narrative

## Technologies Used

- Python 3.10+
- Django 5.x
- Pytest
- SQLite
- HTML / CSS / Tailwind

## Author

MystDoku project created by Michal Pešta, 2025.

