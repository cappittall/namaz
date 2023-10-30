#!/bin/bash

# Activate Python environment
conda activate namaz
cd /home/mendel/namaz

# Perform git pull or any other setup
git pull

# Run Python application
# Attempt to run the first Python script
python /home/mendel/namaz/app.py

# Check if it was successful
if [ $? -eq 0 ]; then
  echo "First script executed successfully."
else
  echo "First script failed. Attempting second script."

  # Attempt to run the second Python script
  python ~/Documents/namaz/app.py

  # Check if the second script was successful
  if [ $? -eq 0 ]; then
    echo "Second script executed successfully."
  else
    echo "Both scripts failed."
  fi
fi
