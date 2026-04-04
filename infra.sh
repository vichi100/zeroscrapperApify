#!/bin/bash

# Configuration
OLLAMA_HOST="http://localhost:11434"
DOCKER_COMPOSE_FILE="docker-compose.yml"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

function check_docker() {
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}Error: Docker is not running. Please start Docker Desktop.${NC}"
        exit 1
    fi
}

function check_ollama() {
    echo "Checking Ollama..."
    if ! curl -s "$OLLAMA_HOST/api/tags" >/dev/null 2>&1; then
        echo -e "${RED}Warning: Ollama is not running at $OLLAMA_HOST.${NC}"
        echo "Attempting to start Ollama..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            open -a Ollama
            sleep 5
        else
            ollama serve &
            sleep 5
        fi
    fi
    
    # Check for the specific model
    MODEL="qwen2.5:1.5b"
    if ! ollama list | grep -q "$MODEL"; then
        echo "Model $MODEL not found. Pulling..."
        ollama pull "$MODEL"
    else
        echo -e "${GREEN}Ollama and model $MODEL are ready.${NC}"
    fi
}

function start() {
    echo "Starting Infrastructure..."
    check_docker
    docker-compose up -d
    check_ollama
    echo -e "${GREEN}Infrastructure is up and running.${NC}"
}

function stop() {
    echo "Stopping Infrastructure..."
    docker-compose down
    
    # Stop uvicorn if running
    PID=$(lsof -t -i :8000)
    if [ -n "$PID" ]; then
        echo "Stopping FastAPI server (PID $PID)..."
        kill $PID
    fi
    
    echo -e "${GREEN}Infrastructure stopped.${NC}"
}

function status() {
    echo "Checking Status..."
    
    # Docker Services
    if docker-compose ps | grep -q "Up"; then
        echo -e "${GREEN}Docker services are running.${NC}"
    else
        echo -e "${RED}Docker services are NOT running.${NC}"
    fi
    
    # Ollama
    if curl -s "$OLLAMA_HOST/api/tags" >/dev/null 2>&1; then
        echo -e "${GREEN}Ollama is running.${NC}"
    else
        echo -e "${RED}Ollama is NOT running.${NC}"
    fi
    
    # FastAPI
    if lsof -i :8000 >/dev/null 2>&1; then
        echo -e "${GREEN}FastAPI server is running on port 8000.${NC}"
    else
        echo -e "${RED}FastAPI server is NOT running.${NC}"
    fi
}

function run_app() {
    echo "Starting FastAPI App..."
    
    # Kill any existing process on port 8000
    PID=$(lsof -t -i :8000)
    if [ -n "$PID" ]; then
        echo "Clearing existing process on port 8000 (PID $PID)..."
        kill -9 $PID
        sleep 2
    fi
    
    if [ ! -d "venv" ]; then
        echo -e "${RED}Error: Virtual environment 'venv' not found. Please create it first.${NC}"
        exit 1
    fi
    source venv/bin/activate
    echo "Logs are being redirected to uvicorn.log (reloads excluded)"
    nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload --reload-exclude "uvicorn.log" > uvicorn.log 2>&1 &
    sleep 2
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    status)
        status
        ;;
    run)
        run_app
        ;;
    *)
        echo "Usage: $0 {start|stop|status|run}"
        exit 1
esac
