# AI Crime Hotspot Predictor and Safe Route System

A small Flask-based backend and static frontend that analyzes area crime profiles and recommends safer routes between locations using a combination of heuristics and (optional) a decision-tree model trained on the included mock dataset.

## Features

- REST API with endpoints to check health, list supported areas, view network overview, and predict safe routes.
- Lightweight frontend served by Flask (templates + static assets).
- Decision-tree model support via scikit-learn (optional — the app falls back to heuristics if scikit-learn isn't available).

## Requirements

- Python 3.11 or 3.12 (recommended). The repository's current environment uses Python 3.15 (alpha), which may not have binary wheels available for `scikit-learn` and `numpy`.
- pip

Install dependencies:

```powershell
# from project root
.venv\\Scripts\\activate
python -m pip install -r requirements.txt
```

If you cannot install `scikit-learn` on your platform, the app will still run using heuristic fallbacks.

## Run

Start the backend server:

```powershell
# from project root
.venv\\Scripts\\activate
python backend/app.py
```

By default the server runs on port `5001`. Visit `http://127.0.0.1:5001/` to open the frontend.

## API

- GET `/api/health` — Returns a simple JSON status.
- GET `/api/supported-areas` — Returns available area names.
- GET `/api/network-overview?time=day|night` — Returns a summary network overview for `day` or `night`.
- POST `/api/predict-route` — Accepts JSON with `start`, `destination`, and optional `time` and returns route analysis.

Example request to predict a route:

```json
POST /api/predict-route
Content-Type: application/json

{
	"start": "Area A",
	"destination": "Area B",
	"time": "day"
}
```

## Data

- `data/raw/karachi_crime_reference_dataset.csv` — mock raw records used to build area profiles.
- `data/processed/karachi_crime_processed.csv` — processed area profiles used by heuristics and the optional ML model.

## Notes & Troubleshooting

- If `pip install -r requirements.txt` fails while building `numpy` or `scikit-learn`, install a stable Python (3.11/3.12) and recreate the virtual environment:

```powershell
# remove existing venv (if any), then create a new one with a stable Python
python -m venv .venv
.venv\\Scripts\\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

- The app includes fallbacks so it will operate without scikit-learn, but route predictions will use heuristic scores rather than trained model outputs.

## Development

- Backend entrypoint: `backend/app.py`.
- API routes: `backend/routes.py`.
- Algorithms: `algorithms/` contains the decision tree, pathfinding, and risk modules.

## License

This project is provided as-is for educational purposes.