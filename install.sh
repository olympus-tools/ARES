#!/bin/bash

# Check and install Python 3, pip, and python3-venv if they are not already installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 not found. Installation starts..."
    sudo_exec apt update
    sudo_exec apt install -y python3
else
    echo "Python 3 is already installed."
fi

if ! command -v python3-pip &> /dev/null; then
    echo "pip for Python 3 not found. Installation starts..."
    sudo_exec apt install -y python3-pip
else
    echo "pip for Python 3 is already installed."
fi

if ! command -v python3 -m venv &> /dev/null; then
    echo "python3-venv not found. Installation starts..."
    sudo_exec apt install -y python3-venv
else
    echo "python3-venv is already installed."
fi

# Install the specific venv package suggested by the error
if ! dpkg -s python3.12-venv &> /dev/null; then
    echo "Installing suggested python3.12-venv package..."
    sudo_exec apt install -y python3.12-venv
fi

# Setting path variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv_lin"

# Check if the virtual environment exists, delete it and recreate it if it does.
if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists. Cleaning it up..."
    rm -rf "$VENV_DIR"
    echo "Creating new virtual environment in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
else
    echo "Creating virtual environment in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

# Use the absolute path to pip in the virtual environment
VENV_PIP="$VENV_DIR/bin/pip"

# Install the project and its dependencies via setup.py
echo "Installing the project and its dependencies using setup.py..."
"$VENV_PIP" install .

# Show all installed libraries
echo "Following libraries are now available in the virtual environment:"
"$VENV_PIP" list