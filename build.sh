#!/bin/bash
echo "Building MeckChat executable for Linux..."
source venv/bin/activate
pyinstaller --onefile --windowed --name MeckChat main.py
echo "Build complete! Executable is located in the dist/ directory."
