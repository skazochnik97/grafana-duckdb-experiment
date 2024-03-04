# grafana-duckdb-experiment

prereq:
OS: Ubuntu 22.04 LTS
2CPU, 4Gb RAM, 8Gb HDD

# Add swap file
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile

# Install PostgreSQL 16 (via https://dev.to/rainbowhat/postgresql-16-installation-on-ubuntu-2204-51ia )
apt update
apt install gnupg2 wget vim apt-transport-https software-properties-common git clang build-essential unzip -y
echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list
curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg
apt update
apt install postgresql-16 postgresql-contrib-16 postgresql-server-dev-16 -y

# Install duckdb extension (via https://github.com/digoal/blog/blob/master/202401/20240124_01.md)

git clone --depth 1 https://github.com/alitrack/duckdb_fdw
cd duckdb_fdw
wget -c https://github.com/duckdb/duckdb/releases/download/v0.9.2/libduckdb-linux-amd64.zip
unzip -o -d . libduckdb-linux-amd64.zip
cp libduckdb.so $(pg_config --libdir)
make USE_PGXS=1
make install USE_PGXS=1

# ###############
# ###############
# ###############
apt install apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
apt update
apt-cache policy docker-ce

# ##############
# Install PostgreSQL 14
apt update
apt install pipx git ansible apt-transport-https software-properties-common clang wget build-essential unzip postgresql-server-dev-14 libsqlite3-dev postgresql -y

# Install Grafana
https://grafana.com/docs/grafana/latest/setup-grafana/installation/debian/
sudo mkdir -p /etc/apt/keyrings/
wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | sudo tee /etc/apt/keyrings/grafana.gpg > /dev/null
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list
apt update
apt-get install grafana

mkdir libduckdb
cd libduckdb
wget -T 36000 -t 0 --waitretry=5 https://github.com/duckdb/duckdb/releases/download/v0.9.2/libduckdb-src.zip
unzip -n -d . libduckdb-src.zip
clang++ -c -fPIC -std=c++11 -D_GLIBCXX_USE_CXX11_ABI=0 duckdb.cpp -o duckdb.o
clang++ -shared -o libduckdb.so *.o

cp libduckdb.so $(pg_config --libdir)

USE_PGXS=1 make
USE_PGXS=1 make install

# Connect to postgres
sudo -u postgres psql -U postgres
postgres=# create extension duckdb_fdw;


################

apt-get install -y git build-essential cmake postgresql-server-dev-16 postgresql-client-16 wget unzip
git clone --depth 1 https://github.com/alitrack/duckdb_fdw
cd duckdb_fdw
wget -c https://github.com/duckdb/duckdb/releases/download/v0.9.2/libduckdb-linux-amd64.zip
unzip -o -d . libduckdb-linux-amd64.zip
cp libduckdb.so $(pg_config --libdir)
make USE_PGXS=1
make install USE_PGXS=1
