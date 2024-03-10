# grafana-duckdb-experiment

# Plan
- [1] The postgres plugin to use is https://github.com/alitrack/duckdb_fdw This plugin needs to be compiled on wsl linux ubuntu.
- [2] once you have duckdb working, and able to read the data from postgres using the plugin, i need you to connect to this data using the postgres datasource in grafana
- [3] build an simple example dashboard grafana showing the key as a dropdown filter, and then a graph showing the value trend (you will see the Key is one of the columns in the parquet, and Interval1Value will be the count for that key)
- 4 reload the duckdb every n minutes so that new parquet files that appear in a directory are automatically added to the duckdb database

prereq:
- `OS: Ubuntu 22.04 LTS`
- `2CPU, 4Gb RAM, 8Gb HDD (t2.medium)`

outcome:
- `PostreSQL 16`
- `duckdb_fdw 1.1`
- `libduckdb 0.9.2`

# Install PostgreSQL 16
```bash
apt update
DEBIAN_FRONTEND=noninteractive apt install gnupg2 wget vim apt-transport-https software-properties-common git clang build-essential unzip p7zip-full python3-pip -y
echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list
curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg
apt update
DEBIAN_FRONTEND=noninteractive apt install postgresql-16 postgresql-contrib-16 postgresql-server-dev-16 -y
```

# Install duckdb extension
```bash
git clone -b main_9x-10x-support --depth 1 https://github.com/ahuarte47/duckdb_fdw
cd duckdb_fdw
wget -c https://github.com/duckdb/duckdb/releases/download/v0.9.2/libduckdb-linux-amd64.zip
unzip -o -d . libduckdb-linux-amd64.zip
cp libduckdb.so $(pg_config --libdir)
make USE_PGXS=1
make install USE_PGXS=1
```

```bash
cd /usr/local/bin
wget https://github.com/duckdb/duckdb/releases/download/v0.10.0/duckdb_cli-linux-amd64.zip
unzip duckdb_cli-linux-amd64.zip
```

# Install extension to postgres
```bash
sudo -u postgres psql -U postgres -c "create extension duckdb_fdw;"
sudo -u postgres psql -U postgres -c "SELECT * FROM pg_available_extensions where name='duckdb_fdw';"
```

# Install Grafana
https://grafana.com/docs/grafana/latest/setup-grafana/installation/debian/
```bash
sudo mkdir -p /etc/apt/keyrings/
wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | sudo tee /etc/apt/keyrings/grafana.gpg > /dev/null
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list
apt update
DEBIAN_FRONTEND=noninteractive apt-get install grafana -y
```

Hint: There is no concurrency because of using file on disk. So when creating postgres datasource set "Auto Max Idle" to off, "Max idle" to 0, "Max lifetime" to 1.

# Set database
```bash
pip install duckdb==0.9.2 pandas

mkdir -p/var/parquet /var/duckdb
mv parquet.7z /var/parquet/
cd /var/parquet
7z e parquet.7z
rm -f parquet.7z
cd /var/duckdb
wget https://raw.githubusercontent.com/skazochnik97/grafana-duckdb-experiment/main/duckdb_load.py
python3 duckdb_load.py
chown postgres /var/duckdb
chown postgres /var/duckdb/database.duckdb
```

# Run every 10 minutes
Run every 10 minutes for example using cron:

```bash
*/10 * * * * /usr/bin/python3 /var/duckdb/duckdb_load.py
```

Script duckdb_load.py will compare list of existing files with loaded from filenames_table table and loads only new ones.

# Set PostgreSQL
```sql
CREATE SERVER duckdb_server FOREIGN DATA WRAPPER duckdb_fdw OPTIONS (database '/var/duckdb/database.duckdb', read_only 'true', keep_connections 'off');

-- show created
select * from pg_foreign_server;
\des+

CREATE FOREIGN TABLE public.aggregations_table (
    Key                    text,
    Interval1Value         int,
    Interval2Value         int,
    Interval3Value         int,
    Interval4Value         int,
    filename               text
)
SERVER duckdb_server
OPTIONS (
    table 'aggregations_table'
);

-- test query
select * from public.aggregations_table limit 10;

```


# Links:
- https://dev.to/rainbowhat/postgresql-16-installation-on-ubuntu-2204-51ia
- https://github.com/alitrack/duckdb_fdw/pull/38
- https://github.com/digoal/blog/blob/master/202401/20240124_01.md
