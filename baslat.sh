#!/usr/bin/env bash

# Manually set PATH to use the namaz environment
export PATH="/home/mendel/.conda/envs/namaz/bin:$PATH"

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
