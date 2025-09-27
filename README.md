# Project-Capital-Backend
Backend portion of the HackGT Project

# Set up the Anaconda Environment

conda env create -f hackgt-env.yaml

conda activate banking-dashboard

# Install mongodb

wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -

echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

sudo apt update

sudo apt install -y mongodb-org

sudo apt install -y mongodb-mongosh


# To open the Mongo DB Database

mongosh

use bank_db


# Run the backend

fastapi dev main.py

show collections
