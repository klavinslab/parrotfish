#!/bin/bash

kill_container() { 
  echo "Killing running container..."
  sudo docker kill $(sudo docker ps -a -q --filter="ancestor=aq")
}

trap kill_container INT

if [ $1 = 'run' ]; then
  # Setup
  rm -rf /tmp/aq-log.txt
  sudo docker kill $(sudo docker ps -a -q --filter="ancestor=aq")

  # Start Aquarium Docker container
  sudo docker run --rm -tp 3001:3000 aq >> /tmp/aq-log.txt &

  # Wait for container to start
  sleep 1
  while ! grep -m1 'INFO  WEBrick::HTTPServer#start:' < /tmp/aq-log.txt; do
    sleep 1
  done
  CID=$(sudo docker ps --latest --quiet)
  echo $CID

elif [ $1 = 'kill' ]; then
  echo "Killing running container..."
  sudo docker kill $2
  #sudo docker kill $(sudo docker ps -a -q --filter="ancestor=aq")
fi

