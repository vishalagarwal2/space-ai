#!/bin/bash


export red="\033[1;31m"
export yellow="\033[1;33m"
export green="\033[1;32m"
export reset_color="\033[0m"

### perform system update 
echo -e "${yellow} performing system update ${reset_color}"
sudo -S apt update
sudo apt install -y curl wget openssh-server net-tools ffmpeg \
  libhdf5-dev libffi-dev qrencode \
  ntp ifmetric dialog \
  zip unzip network-manager traceroute ca-certificates gnupg iperf
sleep 1
echo -e "${green} system update completed ${reset_color}\n"
###


# Api Gateway Setup
echo -e "${yellow} setting up api gateway databases ${reset_color}"
if [ -d "${PWD}/kong_data" ]; then 
  echo -e "${green} api gateway database already present ${reset_color}\n"
else
    docker network create kong-net
    docker pull registry.easemyai.com/redx/redx_postgres:9.6.20-alpine
    docker pull registry.easemyai.com/redx/redx_kong:2.2.0-alpine
    sleep 1
    docker run -d \
        --name kong-database \
        --network=kong-net \
        -p 5432:5432 \
        -e "POSTGRES_USER=kong" \
        -e "POSTGRES_DB=kong" \
        -e "POSTGRES_PASSWORD=kong" \
        -v ${PWD}/kong_data:/var/lib/postgresql/data registry.easemyai.com/redx/redx_postgres:9.6.20-alpine
    sleep 30
    docker run --rm \
        --name bootstrapper \
        --link kong-database:kong-database \
        --network=kong-net \
        -e "KONG_DATABASE=postgres" \
        -e "KONG_PG_HOST=kong-database" \
        -e "KONG_PG_USER=kong" \
        -e "KONG_PG_PASSWORD=kong" registry.easemyai.com/redx/redx_kong:2.2.0-alpine kong migrations bootstrap -v
    sleep 1
    docker rm -f kong-database
    sleep 1
    docker network rm kong-net
    echo -e "${green} api gateway database setup finished ${reset_color}\n"
fi


docker compose up -d

sleep 120

sudo sh kong_setup.sh
