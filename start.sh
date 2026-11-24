#!/bin/bash
# start.sh — Start the full-stack application
set -e
trap 'echo "Shutting down..."; [ -f .pids ] && while IFS= read -r pid; do kill "$pid" 2>/dev/null || true; done < .pids; rm -f .pids; exit 0' SIGINT SIGTERM

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Convert path to native format for Windows programs under Git Bash
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

    # Probe by running it: under Git Bash `python3` may be the Windows Store stub
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

    # Node.js 20.19+/22.12+ (required by vite 7+)
    if command -v node &>/dev/null; then
        NODE_VERSION=$(node --version | sed 's/v//')
        NODE_MAJOR=$(echo $NODE_VERSION | cut -d. -f1)
        NODE_MINOR=$(echo $NODE_VERSION | cut -d. -f2)
        if [ "$NODE_MAJOR" -lt 20 ] || ([ "$NODE_MAJOR" -eq 20 ] && [ "$NODE_MINOR" -lt 19 ]); then
            echo "❌ Node.js 20.19+ or 22.12+ required (found $NODE_VERSION)"
            errors=$((errors+1))
        else
            echo "✓ Node.js $NODE_VERSION"
        fi
    else
        echo "❌ Node.js not found. Install from https://nodejs.org"
        errors=$((errors+1))
    fi

    # npm
    if ! command -v npm &>/dev/null; then
        echo "❌ npm not found"
        errors=$((errors+1))
    else
        echo "✓ npm $(npm --version)"
    fi

    # pip
    if [ -n "$PYTHON" ] && ! "$PYTHON" -m pip --version &>/dev/null; then
        echo "❌ pip not found. Run: $PYTHON -m ensurepip"
        errors=$((errors+1))
    fi

    if [ $errors -gt 0 ]; then
        echo ""
        echo "❌ $errors prerequisite(s) missing. Please install them and retry."
        exit 1
    fi
    echo ""
}

check_prerequisites

# Kill previous PIDs if .pids exists
if [ -f .pids ]; then
    echo "=== Stopping previous instances ==="
    while IFS= read -r pid; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null && echo "  Stopped PID $pid" || true
        fi
    done < .pids
    rm -f .pids
    echo ""
fi

# === Backend Setup ===
BACKEND_DIR="backend"
echo "=== Setting up backend ==="
cd "$BACKEND_DIR"

# Create venv if missing
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    "$PYTHON" -m venv .venv
fi

# Activate venv (Windows Git Bash uses Scripts/, macOS/Linux use bin/)
if [ -f .venv/Scripts/activate ]; then 
    source .venv/Scripts/activate
else 
    source .venv/bin/activate
fi

# Install backend dependencies
echo "Installing backend dependencies..."
pip install . -q

# Copy dev.env to .env if missing
if [ ! -f ".env" ]; then
    echo "Creating .env from dev.env..."
    cp dev.env .env
fi

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Run seed data
echo "Seeding database..."
python app/cli.py seed

# Pick available port for backend
BACKEND_PORT=$(find_available_port 9000)

# Update CORS origins in .env to include frontend ports
# Use portable approach: read, update, write back
FRONTEND_PORT_RANGE="5173,5174,5175"
if ! grep -q "CORS_ORIGINS" .env; then
    echo "CORS_ORIGINS=http://localhost:$FRONTEND_PORT_RANGE" >> .env
else
    # Create temp file for safe sed operation
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|^CORS_ORIGINS=.*|CORS_ORIGINS=http://localhost:5173,http://localhost:5174,http://localhost:5175|" .env
    else
        sed -i "s|^CORS_ORIGINS=.*|CORS_ORIGINS=http://localhost:5173,http://localhost:5174,http://localhost:5175|" .env
    fi
fi

echo "Starting backend on http://localhost:$BACKEND_PORT"
uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT &
BACKEND_PID=$!
cd "$SCRIPT_DIR"

# === Frontend Setup ===
FRONTEND_DIR="frontend"
echo ""
echo "=== Setting up frontend ==="
cd "$FRONTEND_DIR"

# Install frontend dependencies
echo "Installing frontend dependencies..."
npm install -q

# Pick available port for frontend
FRONTEND_PORT=$(find_available_port 5173)

# Start frontend dev server with BACKEND_PORT exported for vite.config.ts
echo "Starting frontend on http://localhost:$FRONTEND_PORT"
BACKEND_PORT="$BACKEND_PORT" npm run dev -- --port "$FRONTEND_PORT" &
FRONTEND_PID=$!
cd "$SCRIPT_DIR"

# Save PIDs
echo "$BACKEND_PID" > .pids
echo "$FRONTEND_PID" >> .pids

echo ""
echo "============================================="
echo "=== Services Running ==="
echo "============================================="
echo "  Backend:  http://localhost:$BACKEND_PORT"
echo "  Frontend: http://localhost:$FRONTEND_PORT"
echo "  API Docs: http://localhost:$BACKEND_PORT/api/docs"
echo ""
echo "=== Default Credentials ==="
echo "  Analyst:"
echo "    Username: analyst1"
echo "    Password: analyst123"
echo ""
echo "  Reviewer:"
echo "    Username: reviewer1"
echo "    Password: reviewer123"
echo ""
echo "Press Ctrl+C to stop all services"
echo "============================================="
wait
