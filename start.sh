#!/bin/bash
# start.sh — Start the Clear Path MVP application
set -e
trap 'echo "Shutting down..."; [ -f .pids ] && while IFS= read -r pid; do kill "$pid" 2>/dev/null || true; done < .pids; rm -f .pids; exit 0' SIGINT SIGTERM

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Portable native path conversion (for Git Bash on Windows)
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

    # Probe Python by running it: under Git Bash `python3` may be the Windows Store stub.
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

    # Node.js 20.19+/22.12+
    if command -v node &>/dev/null; then
        NODE_VERSION=$(node --version | sed 's/v//')
        NODE_MAJOR=$(echo $NODE_VERSION | cut -d. -f1)
        NODE_MINOR=$(echo $NODE_VERSION | cut -d. -f2)
        if [ "$NODE_MAJOR" -lt 20 ] || ([ "$NODE_MAJOR" -eq 20 ] && [ "$NODE_MINOR" -lt 19 ]); then
            if [ "$NODE_MAJOR" -ne 22 ] || [ "$NODE_MINOR" -lt 12 ]; then
                echo "❌ Node.js 20.19+ or 22.12+ required (found $NODE_VERSION)"
                errors=$((errors+1))
            else
                echo "✓ Node.js $NODE_VERSION"
            fi
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

# Stop previous run
if [ -f .pids ]; then
    echo "=== Stopping previous run ==="
    while IFS= read -r pid; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null && echo "  Stopped PID $pid"
        fi
    done < .pids
    rm -f .pids
    echo ""
fi

# Find available ports
BACKEND_PORT=$(find_available_port 9000)
FRONTEND_PORT=$(find_available_port 5173)

echo "=== Setting up backend ==="
cd backend

# Copy dev.env to .env if .env doesn't exist
if [ ! -f .env ]; then
    if [ -f dev.env ]; then
        cp dev.env .env
        echo "Copied dev.env to .env"
    fi
fi

# Create/activate venv
if [ ! -d .venv ]; then
    "$PYTHON" -m venv .venv
    echo "Created virtual environment"
fi

# Windows venvs (Git Bash) have Scripts/, macOS/Linux venvs have bin/
if [ -f .venv/Scripts/activate ]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi

# Install dependencies
echo "Installing dependencies..."
pip install . -q

# Database setup
DB_PATH="$SCRIPT_DIR/backend/app.db"
export DATABASE_URL="sqlite:///$(native_path "$DB_PATH")"

# Run migrations
echo "Running migrations..."
python -m alembic upgrade head

# Run seed data
echo "Seeding database..."
python -m app.seed 2>/dev/null || true

# Update CORS origins in .env before starting
if [ -f .env ]; then
    # Remove existing CORS_ORIGINS line and add new one using sed in-place
    if command -v sed >/dev/null 2>&1; then
        sed -i.bak "/^CORS_ORIGINS=/d" .env 2>/dev/null || sed -i '' "/^CORS_ORIGINS=/d" .env 2>/dev/null || true
        rm -f .env.bak
    fi
    echo "CORS_ORIGINS=http://localhost:$FRONTEND_PORT" >> .env
fi

# Start backend
echo "Starting backend on http://localhost:$BACKEND_PORT"
python -m uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT &
BACKEND_PID=$!
echo "$BACKEND_PID" > "$SCRIPT_DIR/.pids"

cd "$SCRIPT_DIR"

# Setup frontend
echo ""
echo "=== Setting up frontend ==="
cd frontend

echo "Installing dependencies..."
npm install -q

echo "Starting frontend on http://localhost:$FRONTEND_PORT"
BACKEND_PORT="$BACKEND_PORT" npm run dev -- --port "$FRONTEND_PORT" &
FE_PID=$!
echo "$FE_PID" >> "$SCRIPT_DIR/.pids"

cd "$SCRIPT_DIR"

echo ""
echo "=========================================="
echo "=== Clear Path MVP is now running ==="
echo "=========================================="
echo ""
echo "Services:"
echo "  Backend:  http://localhost:$BACKEND_PORT"
echo "  Frontend: http://localhost:$FRONTEND_PORT"
echo "  API Docs: http://localhost:$BACKEND_PORT/docs"
echo ""
echo "Default Credentials:"
echo "  Customer:"
echo "    Email:    admin@example.com"
echo "    Password: admin123"
echo ""
echo "  Colleague:"
echo "    Email:    colleague@example.com"
echo "    Password: colleague123"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

wait
