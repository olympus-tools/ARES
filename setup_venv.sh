#!/bin/bash

# define name of the virtual environment
VENV_DIR=".venv"
SKIP_VENV_SETUP=$1

#####
## FUNCTIONS
#####
# Check if pyproject.toml exists and install dependencies
function install_venv() {
    PRJ_FILE="pyproject.toml"
    if [ -f "$PRJ_FILE" ]; then
        echo "Installing dependencies from '$PRJ_FILE'..."

        if [ -f ".git" ]; then
            pip install -e .
        else
            SETUPTOOLS_SCM_PRETEND_VERSION_FOR_ARES="0.0.1" pip install -e .
        fi

        if [ $? -ne 0 ]; then
            echo "Error: Failed to install dependencies."
        fi
    else
        echo "Warning: '$PRJ_FILE' not found. Skipping dependency installation."
    fi
}

#####
## EXECUTION
#####

# Check if the virtual environment directory already exists
if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment '$VENV_DIR' already exists."
else
    echo "Creating virtual environment '$VENV_DIR'..."
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment."
    fi
fi

# Activate the virtual environment
echo "Activating the virtual environment..."
source "$VENV_DIR/bin/activate"

if [[ $SKIP_VENV_SETUP != "true" ]]; then
    install_venv
fi

echo "Setup complete. The virtual environment is now active."


