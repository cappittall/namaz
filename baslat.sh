#!/usr/bin/env bash

# Initialize conda
eval "$(/var/Miniforge3/bin/conda shell.bash hook)"

#change to the folder
cd /home/mendel/namaz
git pull

# Run Python application
# Attempt to run the first Python script
python /home/mendel/namaz/app.py

# Check if it was successful
if [ $? -eq 0 ]; then
  echo "First script executed successfully."
else
  echo "First script failed. Attempting second script."
  conda activate namaz2
  # Attempt to run the second Python script
  python ~/Documents/namaz/app.py

  # Check if the second script was successful
  if [ $? -eq 0 ]; then
    echo "Second script executed successfully."
  else
    echo "Both scripts failed."
  fi
fi
