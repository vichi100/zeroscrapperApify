# Apify Integrated Server

A simple FastAPI server to trigger and manage [Apify](https://apify.com) actors.

## Setup

1.  **Clone the repository** (if you haven't already).
2.  **Create a virtual environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure environment variables**:
    - Add your `APIFY_API_TOKEN` to the `.env` file.

## Running the Server

Start the server using `uvicorn`:

```bash
uvicorn main:app --reload
```

The server will be available at `http://localhost:8000`.

## API Endpoints

### Health Check
- **URL**: `GET /`
- **Description**: Verifies the server is running.

### Run Actor
- **URL**: `POST /run-actor`
- **Body**:
  ```json
  {
    "actor_id": "apify/web-scraper",
    "run_input": { ...Actor specific input... }
  }
  ```
- **Returns**: `run_id` and status URL.

### Get Results
- **URL**: `GET /results/{run_id}`
- **Description**: Fetches items from the dataset of a specific run.
- **Query Params**: `limit` (default 100).

## Requirements
- Python 3.8+
- Apify Account & API Token
