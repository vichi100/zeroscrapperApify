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

## Infrastructure Management

You can use the provided `infra.sh` script to manage the required services (MongoDB, Redis, Qdrant, and Ollama).

```bash
# Check status of all services
./infra.sh status

# Start all services (Docker + Ollama)
./infra.sh start

# Stop all services and the FastAPI server
./infra.sh stop
```

## Running the Server

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

## Testing Queries

You can test natural language queries using the `test_query.py` script.

### Unit Testing (Parsing & URL Generation)
This tests the extraction of location, BHK, and rent without requiring the full search flow.
```bash
source venv/bin/activate
python3 test_query.py "I am looking for a 2bhk in Andheri West in 40-60k rent" --unit
```

### Direct Scraping (Apify Actor)
This triggers the Apify actor directly using the generated URL and prints the raw JSON results and count.
```bash
source venv/bin/activate
python3 test_query.py "I am looking for a 2bhk in Andheri West in 40-60k rent" --scrape --source nobroker --limit 5
```

### Direct Scraping (MagicBricks)
This triggers the MagicBricks Apify actor and prints the raw JSON results and count.
```bash
source venv/bin/activate
python3 test_query.py "I am looking for a 2bhk in Andheri West in 40-60k rent" --scrape --source magicbricks --limit 5
```

### API Integration Testing
This tests the full flow by sending a request to the running FastAPI server.
```bash
# Ensure infrastructure is running first
./infra.sh start
./infra.sh run

# Run the test
source venv/bin/activate
python3 test_query.py "I am looking for a 2bhk in Andheri West in 40-60k rent" --api
```

## Requirements
- Python 3.8+
- Apify Account & API Token
