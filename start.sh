#!/bin/bash
# start.sh — Start the full-stack application
set -e
trap 'echo "Shutting down..."; [ -f .pids ] && while IFS= read -r pid; do kill "$pid" 2>/dev/null || true; done < .pids; rm -f .pids; exit 0' SIGINT SIGTERM

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Convert Windows paths to Unix format if cygpath is available
native_path() { if command -v cygpath >/dev/null 2>&1; then cygpath -m "$1"; else printf '%s' "$1"; fi; }

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

    if [ -f "frontend/package.json" ]; then
        if command -v node &>/dev/null; then
            NODE_VERSION=$(node --version | sed 's/v//')
            NODE_MAJOR=$(echo $NODE_VERSION | cut -d. -f1)
            if [ "$NODE_MAJOR" -lt 22 ]; then
                echo "❌ Node.js 22.12+ required (found $NODE_VERSION)"
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
    fi

    if [ $errors -gt 0 ]; then
        echo "❌ $errors prerequisite(s) missing. Please install them and retry."
        exit 1
    fi
    echo ""
}

check_prerequisites

# Kill any stale PIDs from previous runs
if [ -f .pids ]; then
    echo "Cleaning up stale PIDs from previous run..."
    while IFS= read -r pid; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null && echo "  Stopped PID $pid" || true
        fi
    done < .pids
    rm -f .pids
fi

# Backend
BACKEND_DIR="backend"
echo "=== Setting up backend ==="
cd "$BACKEND_DIR"

# Copy dev.env to .env if .env doesn't exist
if [ ! -f .env ]; then
    if [ -f dev.env ]; then
        cp dev.env .env
        echo "✓ Created .env from dev.env"
    fi
fi

# Create virtual environment if needed
if [ ! -d ".venv" ]; then
    "$PYTHON" -m venv .venv
    echo "✓ Virtual environment created"
fi

# Windows venvs (Git Bash) have Scripts/, macOS/Linux venvs have bin/
if [ -f .venv/Scripts/activate ]; then 
    source .venv/Scripts/activate
else 
    source .venv/bin/activate
fi

# Install backend dependencies
echo "Installing backend dependencies..."
pip install . -q
echo "✓ Backend dependencies installed"

# Run Alembic migrations
echo "Running database migrations..."
alembic upgrade head
echo "✓ Database schema ready"

# Run seed data
echo "Seeding database..."
python -c "from app.seed import seed_database; seed_database()" 2>/dev/null || true
echo "✓ Seed data loaded"

BACKEND_PORT=$(find_available_port 9000)
echo "✓ Backend will use port $BACKEND_PORT"

# Database path for SQLite (convert for Windows native programs)
DB_PATH="$SCRIPT_DIR/backend/app.db"
export DATABASE_URL="sqlite:///$(native_path "$DB_PATH")"

# Start backend
echo "Starting backend server..."
uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT > "$SCRIPT_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
cd "$SCRIPT_DIR"
echo "$BACKEND_PID" > .pids
echo "✓ Backend started (PID: $BACKEND_PID)"

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:$BACKEND_PORT/api/v1/health >/dev/null 2>&1; then
        echo "✓ Backend is ready"
        break
    fi
    sleep 1
done

# Frontend
FE_DIR="frontend"
if [ -d "$FE_DIR" ] && [ -f "$FE_DIR/package.json" ]; then
    echo ""
    echo "=== Setting up frontend ==="
    cd "$FE_DIR"
    
    # Install frontend dependencies if needed
    if [ ! -d node_modules ]; then
        echo "Installing frontend dependencies..."
        npm install -q
        echo "✓ Frontend dependencies installed"
    fi

    FRONTEND_PORT=$(find_available_port 5173)
    echo "✓ Frontend will use port $FRONTEND_PORT"

    # CORS origins for backend (both localhost and 127.0.0.1 for IPv4/IPv6 compatibility)
    if [ -f "$SCRIPT_DIR/backend/.env" ]; then
        # Check if CORS_ORIGINS is already set
        if ! grep -q "^CORS_ORIGINS=" "$SCRIPT_DIR/backend/.env"; then
            echo "CORS_ORIGINS=http://localhost:$FRONTEND_PORT,http://127.0.0.1:$FRONTEND_PORT" >> "$SCRIPT_DIR/backend/.env"
            echo "✓ Updated CORS_ORIGINS in backend/.env"
        fi
    fi

    # The browser calls a relative /api; vite.config.ts proxies it to BACKEND_PORT
    echo "Starting frontend server..."
    BACKEND_PORT="$BACKEND_PORT" npm run dev -- --port "$FRONTEND_PORT" > "$SCRIPT_DIR/frontend.log" 2>&1 &
    FE_PID=$!
    cd "$SCRIPT_DIR"
    echo "$FE_PID" >> .pids
    echo "✓ Frontend started (PID: $FE_PID)"
fi

# Complete
echo ""
echo "==================================="
echo "✓ Application started successfully!"
echo "==================================="
echo ""
echo "Frontend: http://localhost:$FRONTEND_PORT"
echo "Backend:  http://localhost:$BACKEND_PORT"
echo "API Docs: http://localhost:$BACKEND_PORT/api/v1/docs"
echo ""
echo "=== Default Credentials ==="
echo "  Email:    sasha.patel@gmail.com"
echo "  Password: Demo1234!"
echo "  Passcode: 123456"
echo ""
echo "Logs:"
echo "  Backend:  backend.log"
echo "  Frontend: frontend.log"
echo ""
echo "Press Ctrl+C to stop all services"
wait
