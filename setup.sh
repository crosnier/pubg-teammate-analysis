#!/usr/bin/env bash
# ==============================
# setup.sh - one-click Linux/WSL2 setup
# ==============================
# Run from the project root after `git pull`:
#   ./setup.sh
# Creates the virtual environment, installs dependencies, sets up .env if
# missing, and runs doctor.py to confirm everything is healthy.

set -euo pipefail

write_step() {
    echo ""
    echo -e "\033[36m==> $1\033[0m"
}

EXPECTED_VERSION=""
if [ -f ".python-version" ]; then
    EXPECTED_VERSION=$(cat .python-version)
fi
EXPECTED_MAJOR_MINOR=$(echo "$EXPECTED_VERSION" | cut -d. -f1,2)

write_step "Locating Python ${EXPECTED_VERSION}"
PYTHON_CMD=""
for candidate in "python${EXPECTED_MAJOR_MINOR}" "python3" "python"; do
    if command -v "$candidate" >/dev/null 2>&1; then
        PYTHON_CMD="$candidate"
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo -e "\033[31mNo Python interpreter found on PATH. Install Python ${EXPECTED_VERSION} first.\033[0m"
    exit 1
fi
echo "Using: $PYTHON_CMD"

write_step "Creating virtual environment (.venv)"
if [ ! -d ".venv" ]; then
    "$PYTHON_CMD" -m venv .venv
else
    echo ".venv already exists, skipping creation"
fi

write_step "Activating virtual environment"
# shellcheck disable=SC1091
source .venv/bin/activate

write_step "Installing dependencies"
pip install -r requirements.txt

write_step "Setting up .env"
if [ ! -f ".env" ]; then
    cp ".env.example" ".env"
    echo -e "\033[33m.env created from .env.example - add your PUBG_API_KEY before running main.py\033[0m"
else
    echo ".env already exists, skipping"
fi

write_step "Running environment doctor"
set +e
python doctor.py
DOCTOR_EXIT_CODE=$?
set -e

if [ "$DOCTOR_EXIT_CODE" -eq 0 ]; then
    echo ""
    echo -e "\033[32mSetup complete. Try it out:\033[0m"
    echo -e "\033[32m  python solo.py PlayerName\033[0m"
    echo -e "\033[32m  python squad.py YourName Teammate1 Teammate2\033[0m"
    echo -e "\033[32m(python main.py PlayerName gives the full raw stats dump instead)\033[0m"
else
    echo ""
    echo -e "\033[33mSetup finished but the doctor found issues - see above.\033[0m"
fi

exit $DOCTOR_EXIT_CODE
