#!/bin/bash

echo "Country Image Downloader"
echo "----------------------"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH."
    echo "Please install Python from https://www.python.org/downloads/"
    echo
    read -p "Press Enter to continue..."
    exit 1
fi

# Check if requirements are installed
echo "Checking requirements..."
if ! python3 -c "import selenium" &> /dev/null; then
    echo "Installing requirements..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error installing requirements."
        read -p "Press Enter to continue..."
        exit 1
    fi
fi

echo
echo "Starting the downloader..."
echo

# Run the script
python3 country_image_downloader.py "$@"

echo
if [ $? -ne 0 ]; then
    echo "An error occurred while running the script."
else
    echo "Download completed successfully!"
fi

read -p "Press Enter to continue..."