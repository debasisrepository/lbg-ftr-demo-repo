#!/bin/bash
# start.sh — Start the full-stack application
set -e
trap 'echo "Shutting down..."; [ -f .pids ] && while IFS= read -r pid; do kill "$pid" 2>/dev/null || true; done < .pids; rm -f .pids; exit 0' SIGINT SIGTERM

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
cd "$PROJECT_ROOT"

# Convert path to native Windows format under Git Bash
native_path() { 
    if command -v cygpath >/dev/null 2>&1; then 
        cygpath -m "$1"
    else 
        printf '%s' "$1"
    fi
}

# Port detection (lsof on macOS/Linux, netstat under Git Bash on Windows)
port_in_use() {
    if command -v lsof >/dev/null 2>&1; then
        lsof -iTCP:"$1" -sTCP:LISTEN -t >/dev/null 2>&1
    else
        netstat -an 2>/dev/null | grep -Eq "[:.]$1[[:space:]].*LISTEN"
    fi
}

find_available_port() {
    local port=$1
    while port_in_use "$port"; do
        echo "Port $port in use, trying $((port+1))..." >&2
        port=$((port+1))
    done
    echo $port
}

# === Prerequisite checks ===
check_prerequisites() {
    local errors=0
    echo "=== Checking prerequisites ==="

    # Probe by running it: under Git Bash `python3` may be the Windows Store stub.
    PYTHON=""
    for c in python3 python; do
        if "$c" -c 'import sys' >/dev/null 2>&1; then PYTHON=$c; break; fi
    done
    if [ -n "$PYTHON" ]; then
        PYTHON_VERSION=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
        if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
            echo "❌ Python 3.11+ required (found $PYTHON_VERSION)"
            errors=$((errors+1))
        else
            echo "✓ Python $PYTHON_VERSION"
        fi
    else
        echo "❌ Python 3 not found. Install from https://python.org"
        errors=$((errors+1))
    fi

    if command -v node &>/dev/null; then
        NODE_VERSION=$(node --version | sed 's/v//')
        NODE_MAJOR=$(echo $NODE_VERSION | cut -d. -f1)
        if [ "$NODE_MAJOR" -lt 20 ]; then
            echo "❌ Node.js 20+ required (found $NODE_VERSION)"
            errors=$((errors+1))
        else
            echo "✓ Node.js $NODE_VERSION"
        fi
    else
        echo "❌ Node.js not found. Install from https://nodejs.org"
        errors=$((errors+1))
    fi

    if ! command -v npm &>/dev/null; then
        echo "❌ npm not found"
        errors=$((errors+1))
    else
        echo "✓ npm $(npm --version)"
    fi

    if [ $errors -gt 0 ]; then
        echo ""
        echo "❌ $errors prerequisite(s) missing. Please install them and retry."
        exit 1
    fi
    echo ""
}

check_prerequisites

# Clean up previous run
if [ -f .pids ]; then
    echo "Stopping previous run..."
    while IFS= read -r pid; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done < .pids
    rm -f .pids
fi

echo "=== LBG FTR Demo - Digital Banking Payment Journey Platform ==="
echo ""

# Backend setup
BACKEND_DIR="$PROJECT_ROOT/backend"
echo "=== Setting up backend ==="
cd "$BACKEND_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d .venv ]; then
    echo "Creating Python virtual environment..."
    "$PYTHON" -m venv .venv
fi

# Activate virtual environment (Windows venvs have Scripts/, macOS/Linux have bin/)
if [ -f .venv/Scripts/activate ]; then 
    source .venv/Scripts/activate
else 
    source .venv/bin/activate
fi

# Install dependencies
echo "Installing backend dependencies..."
pip install --quiet --upgrade pip
pip install --quiet .

# Create .env from dev.env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env from dev.env..."
    cp dev.env .env
fi

# Database — default to SQLite with absolute path
DB_PATH="$BACKEND_DIR/app.db"
export DATABASE_URL="${DATABASE_URL:-sqlite:///$(native_path "$DB_PATH")}"
echo "Database: $DATABASE_URL"

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Run seed data
echo "Loading seed data..."
python -m app.seed

# Find available backend port
BACKEND_PORT=$(find_available_port 9000)
echo "Starting backend server on port $BACKEND_PORT..."

# Start backend
uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT > ../backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "$PROJECT_ROOT/.pids"

# Wait for backend to be ready
echo "Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:$BACKEND_PORT/health > /dev/null 2>&1; then
        echo "✓ Backend is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "ERROR: Backend failed to start"
        if [ -f "$PROJECT_ROOT/backend.log" ]; then
            cat "$PROJECT_ROOT/backend.log"
        else
            echo "(No backend.log found)"
        fi
        exit 1
    fi
    sleep 1
done

cd "$PROJECT_ROOT"

# Frontend setup
FRONTEND_DIR="$PROJECT_ROOT/frontend"
if [ -d "$FRONTEND_DIR" ] && [ -f "$FRONTEND_DIR/package.json" ]; then
    echo ""
    echo "=== Setting up frontend ==="
    cd "$FRONTEND_DIR"
    
    echo "Installing frontend dependencies..."
    npm install --quiet

    # Find available frontend port
    FRONTEND_PORT=$(find_available_port 5173)
    
    # The browser calls a relative /api; vite.config.ts proxies it to BACKEND_PORT.
    echo "Starting frontend on port $FRONTEND_PORT..."
    BACKEND_PORT="$BACKEND_PORT" npm run dev -- --port "$FRONTEND_PORT" > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID >> "$PROJECT_ROOT/.pids"
    
    cd "$PROJECT_ROOT"
fi

echo ""
echo "=== Application Started Successfully ==="
echo ""
echo "Backend API:       http://localhost:$BACKEND_PORT"
echo "API Documentation: http://localhost:$BACKEND_PORT/api/docs"
if [ -n "$FRONTEND_PORT" ]; then
    echo "Frontend:          http://localhost:$FRONTEND_PORT"
fi
echo ""
echo "=== Default Credentials ==="
echo "  Admin:    admin@example.com / admin123"
echo "  Personal: john.smith@example.com / Personal123!"
echo "  Business: jane.doe@businessexample.com / Business123!"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for processes
wait
