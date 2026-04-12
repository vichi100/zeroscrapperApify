# Housing.com High-Fidelity Scraper Pipeline

A professional, WAF-resistant real estate search engine and background enrichment pipeline.

## ⚙️ Backend Services

To start the entire backend stack (API + Background Worker) with a single command:

```bash
./infra.sh run
```

This will:
1.  Clear any existing processes on port 8000.
2.  Start the FastAPI server in the background.
3.  Start the BullMQ worker in the background.

To stop everything: `./infra.sh stop`
To check status: `./infra.sh status`

---

## 📡 API Endpoints

### 1. Trigger Search & Scrape
**POST** `/search`
```json
{
  "user_id": "vichi_001",
  "post_content": "2bhk rent in andheri west under 70k"
}
```

### 2. Check Job Status
**GET** `/status/{requirement_id}`
Returns the lifecycle status (`pending`, `processing`, `completed`, `failed`) and any error details.

---

## 🏗️ Architecture

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



python3 normalize_nobroker_util.py
