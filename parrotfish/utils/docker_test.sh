#!/bin/bash

# Setup
rm -rf /tmp/aq-log.txt

# Start Aquarium Docker container
echo "Killing running container..."
sudo docker kill $(sudo docker ps -aq)
echo "Starting aquarium container..."
sudo docker run --rm -tp 3000:3000 aq >> /tmp/aq-log.txt &

# Run protocol test
sleep 1
while ! grep -m1 'INFO  WEBrick::HTTPServer#start:' < /tmp/aq-log.txt; do
  sleep 1
done
echo 'Aquarium container started!'

echo 'Running protocol test...'
pipenv run python trident_test.py
