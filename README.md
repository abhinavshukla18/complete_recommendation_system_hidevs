# Complete Recommendation System

A recommendation system for learning content. It has a SQLite database, a
recommendation engine with four strategies, and a Flask REST API.

## Project structure

```
Complete_reco_sys/
  data/        database.py, models.py (6 tables), repositories.py
  engine/      orchestrator.py, similarity.py, candidate_gen.py,
               scorer.py, evaluator.py
  api/         app.py (Flask API)
  scripts/     seed_data.py, evaluate.py, load_test.py
  tests/       conftest.py, test_data.py, test_engine.py, test_api.py
  requirements.txt
  evaluation_report.md
```

## Setup (Windows PowerShell)

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m scripts.seed_data
```

The last command creates `recommendations.db` and fills it with a sample
dataset (12 users, 24 content items, 64 interactions).

## Run the API

```
python -m api.app
```

The API runs at http://127.0.0.1:5000.

To require an API key, set it before starting the server:

```
$env:API_KEY = "mysecret"
python -m api.app
```

Then send it in an `X-API-Key` header. `/health` never needs a key.

## Endpoints

| Method | Path | What it does |
|---|---|---|
| GET | `/recommend/<user_id>?limit=5` | Recommendations for a user (limit 1-50) |
| POST | `/feedback` | Record feedback |
| GET | `/health` | Health check |
| GET | `/metrics` | Request count, errors, average response time, cache stats |

Every endpoint returns JSON. Errors look like
`{"error": "...", "request_id": "..."}`. Status codes: 400 for bad input,
401 for a missing or wrong API key, 404 for an unknown user, content item or
route.

Example feedback body:

```json
{"user_id": 1, "content_id": 3, "type": "like", "rating": 5}
```

`type` is required (for example `like`, `complete`, `rating`, `view`).
`rating` is optional.

Every response has an `X-Request-ID` header for tracing. You can send your
own `X-Request-ID` and it will be reused.

## How recommendations work

1. Four strategies find candidates: collaborative, content-based,
   skill-based and popular.
2. A scorer ranks them using relevance (0.5), agreement between strategies
   (0.3) and popularity (0.2).
3. Each result includes a short explanation of why it was recommended.
4. New users with no history get skill-based and popular recommendations
   (cold start).
5. Results are cached in memory. Recording feedback reloads the data and
   clears the cache, so new feedback changes later recommendations.

## Run the tests

```
python -m pytest -q
```

To see test coverage:

```
python -m pytest --cov=api --cov=engine --cov=data --cov-report=term-missing -q
```

## Evaluation

```
python -m scripts.evaluate
```

This hides each user's last positive item, rebuilds the engine without it
(in a temporary in-memory database), and checks whether the engine brings it
back. It prints Precision@5, Recall@5 and NDCG@5 and writes
`evaluation_report.md`.

## Load test

Start the API in one terminal, then in a second terminal run:

```
python -m scripts.load_test
```

It simulates 10 users sending requests at the same time and adds the
results to `evaluation_report.md`. Run `scripts.evaluate` first, because it
creates the report file from scratch.

## Results

See `evaluation_report.md` for the full accuracy and load test tables.