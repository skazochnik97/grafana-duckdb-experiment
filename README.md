# grafana-duckdb-experiment

# Plan
- [1] The postgres plugin to use is https://github.com/alitrack/duckdb_fdw This plugin needs to be compiled on wsl linux ubuntu.
- [2] once you have duckdb working, and able to read the data from postgres using the plugin, i need you to connect to this data using the postgres datasource in grafana
- 3 build an simple example dashboard grafana showing the key as a dropdown filter, and then a graph showing the value trend (you will see the Key is one of the columns in the parquet, and Interval1Value will be the count for that key)

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
DEBIAN_FRONTEND=noninteractive apt install gnupg2 wget vim apt-transport-https software-properties-common git clang build-essential unzip p7zip-full -y
echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list
curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg
apt update
DEBIAN_FRONTEND=noninteractive apt install postgresql-16 postgresql-contrib-16 postgresql-server-dev-16 -y
```

Add to the end of the config /etc/postgresql/16/main/pg_hba.conf:
```
host        all           all      127.0.0.1/32    md5
```

then execute: SELECT pg_reload_conf();

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
rm duckdb_cli-linux-amd64.zip
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

fix in the config /etc/grafana/grafana.ini:
```ini
[security]
admin_user = admin
admin_password = admin
[users]
allow_sign_up = false
allow_org_create = false
```
Run:
```bash
systemctl start grafana-server
```

# Set database
```bash
mkdir /var/parquet
mv parquet.7z /var/parquet/
cd /var/parquet
7z e parquet.7z
rm -f parquet.7z
```

At sudo -u postgres psql -U postgres run:
```sql
CREATE SERVER duckdb_server FOREIGN DATA WRAPPER duckdb_fdw OPTIONS (database ':memory:');
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
    table 'read_parquet("/var/parquet/Aggregations_*.parquet", filename=true)'
);
select * from public.aggregations_table limit 10;
```

And for raw tables the same way:
```sql
CREATE FOREIGN TABLE public.CISCORouterLog (
    "STRING"                text,
    "CRITICALITY"           text,
    "TABLE"                 text,
    "ACTION"                text,
    "HOSTNAME"              text
)
SERVER duckdb_server
OPTIONS (
    table 'read_parquet("/var/parquetraw/CISCORouterLog_*.parquet", filename=true)'
);

-- check
select * from public.CISCORouterLog limit 10;

CREATE FOREIGN TABLE public.IPTablesFirewall (
    "INTERFACE"                 text,
    "DSTADDR"                   text,
    "SRCPORT"                   text,
    "PROTO"                     text,
    "ACTION"                    text,
    "STRINGS"                   text,
    "OUT"                       text,
    "MAC"                       text,
    "LEN"                       text,
    "TOS"                       text,
    "PREC"                      text,
    "TTL"                       text,
    "ID"                        text,
    "WINDOW"                    text,
    "RES"                       text,
    "URGP"                      text,
    "TABLE"                     text,
    "SRCADDR"                   text,
    "DSTPORT"                   text,
    "HOSTNAME"                  text
)
SERVER duckdb_server
OPTIONS (
    table 'read_parquet("/var/parquetraw/IPTablesFirewall_*.parquet", filename=true)'
);

CREATE FOREIGN TABLE public.LinuxAudit (
"EGID"                         text,
"PROCESS"                      text,
"TABLE"                        text,
"EVENTCOUNT"                   text,
"STRINGS"                      text,
"RUID"                         text,
"EUID"                         text,
"RGID"                         text,
"RETURNCODE"                   text,
"SUCCESS"                      text,
"EVENTID"                      text,
"TARGET"                       text,
"HOSTNAME"                     text
)
SERVER duckdb_server
OPTIONS (
    table 'read_parquet("/var/parquetraw/LinuxAudit_*.parquet", filename=true)'
);

CREATE FOREIGN TABLE public.MSSQLLog (
 "EVENTID"                    text,
 "DBNAME"                     text,
 "TABLE"                      text,
 "STRINGS"                    text,
 "SPID"                       text,
 "USERNAME"                   text,
 "CLASS"                      text,
 "TARGETLOGINNAME"            text,
 "DBUSERNAME"                 text,
 "ROLENAME"                   text,
 "TARGETUSERNAME"             text,
 "HOSTNAME"                   text
)
SERVER duckdb_server
OPTIONS (
    table 'read_parquet("/var/parquetraw/MSSQLLog_*.parquet", filename=true)'
);

CREATE FOREIGN TABLE public.PANFirewall (
"SOURCEZONE"                  text,
"TABLE"                       text,
"BYTES"                       text,
"NATSRCIP"                    text,
"BYTESIN"                     text,
"NATDESTPORT"                 text,
"LOGFORWARDINGPROFILE"        text,
"ELAPSEDTIME"                 text,
"NATDSTIP"                    text,
"INGRESSINTERFACE"            text,
"SERIALNUMBER"                text,
"VIRTUALSYSTEM"               text,
"DSTADDR"                     text,
"ACTION"                      text,
"PACKETS"                     text,
"DSTPORT"                     text,
"NATSOURCEPORT"               text,
"CATEGORY"                    text,
"EGRESSINTERFACE"             text,
"DESTINATIONZONE"             text,
"RULENAME"                    text,
"SRCADDR"                     text,
"BYTESOUT"                    text,
"REPEATCOUNT"                 text,
"SRCPORT"                     text,
"VERSION"                     text,
"TYPE"                        text,
"FLAGS"                       text,
"URLCATEGORY"                 text,
"APPLICATION"                 text,
"SESSIONID"                   text,
"HOSTNAME"                    text
)
SERVER duckdb_server
OPTIONS (
    table 'read_parquet("/var/parquetraw/PANFirewall_*.parquet", filename=true)'
);

CREATE FOREIGN TABLE public.PIXLog (
 "SRCADDR"                    text,
 "CRITICALITY"                text,
 "SRCPORT"                    text,
 "ACTION"                     text,
 "PROTO"                      text,
 "EVENTID"                    text,
 "DSTPORT"                    text,
 "DSTADDR"                    text,
 "TABLE"                      text,
 "STRING"                     text,
 "HOSTNAME"                   text
)
SERVER duckdb_server
OPTIONS (
    table 'read_parquet("/var/parquetraw/PIXLog_*.parquet", filename=true)'
);

CREATE FOREIGN TABLE public.SnareServerLog (
"RETURN"                     text,
"TABLE"                      text,
"SOURCE"                     text,
"ACTION"                     text,
"USERNAME"                   text,
"RESOURCE"                   text,
"HOSTNAME"                   text
)
SERVER duckdb_server
OPTIONS (
    table 'read_parquet("/var/parquetraw/SnareServerLog_*.parquet", filename=true)'
);

CREATE FOREIGN TABLE public.SolarisBSM (
 "EVENTID"                   text,
 "EVENTCOUNT"                text,
 "EUID"                      text,
 "EGID"                      text,
 "TABLE"                     text,
 "STRINGS"                   text,
 "AUID"                      text,
 "RETURNCODE"                text,
 "RUID"                      text,
 "RGID"                      text,
 "PID"                       text,
 "TARGET"                    text,
 "HOSTNAME"                  text
)
SERVER duckdb_server
OPTIONS (
    table 'read_parquet("/var/parquetraw/SolarisBSM_*.parquet", filename=true)'
);

-- broken table: has duplicate column name "PROTO"
CREATE FOREIGN TABLE public.SonicWall (
 "PRIORITY"                  text,
 "SRCPORT"                   text,
 "CATEGORY"                  text,
 "SRCADDR"                   text,
 "DSTPORT"                   text,
 "c"                         text,
 "n"                         text,
 "srcInt"                    text,
 "dstDNS"                    text,
 "dstInt"                    text,
 "srcMac"                    text,
 "dstMac"                    text,
 "proto"                     text,
 "TABLE"                     text,
 "MESSAGE"                   text,
 "DSTADDR"                   text,
 "EVENTID"                   text,
 "PROTO"                     text,
 "FWADDR"                    text,
 "app"                       text,
 "sid"                       text,
 "appcat"                    text,
 "appid"                     text,
 "catid"                     text,
 "appName"                   text,
 "note"                      text,
 "HOSTNAME"                  text
)
SERVER duckdb_server
OPTIONS (
    table 'read_parquet("/var/parquetraw/SonicWall_*.parquet", filename=true)'
);

CREATE FOREIGN TABLE public.WebLog (
 "URL"                       text,
 "TABLE"                     text,
 "STRINGS"                   text,
 "HOSTNAME"                  text,
 "RETURNCODE"                text,
 "AGENT"                     text,
 "PROTOCOL"                  text,
 "LOGTYPE"                   text,
 "REFERRER"                  text
)
SERVER duckdb_server
OPTIONS (
    table 'read_parquet("/var/parquetraw/WebLog_*.parquet", filename=true)'
);

CREATE FOREIGN TABLE public.WinApplication (
 "SOURCETYPE"                text,
 "STRINGS"                   text,
 "TABLE"                     text,
 "DATA"                      text,
 "EVENTCOUNT"                text,
 "EVENTID"                   text,
 "SOURCE"                    text,
 "USER"                      text,
 "RETURN"                    text,
 "HOSTNAME"                  text
)
SERVER duckdb_server
OPTIONS (
    table 'read_parquet("/var/parquetraw/WinApplication_*.parquet", filename=true)'
);

CREATE FOREIGN TABLE public.WinSecurity (
 "SOURCE"                    text,
 "SOURCETYPE"                text,
 "USER"                      text,
 "STRINGS"                   text,
 "TABLE"                     text,
 "EVENTID"                   text,
 "RETURN"                    text,
 "EVENTCOUNT"                text,
 "HOSTNAME"                  text

)
SERVER duckdb_server
OPTIONS (
    table 'read_parquet("/var/parquetraw/WinSecurity_*.parquet", filename=true)'
);

CREATE FOREIGN TABLE public.WinSystem (
 "STRINGS"                   text,
 "SOURCE"                    text,
 "TABLE"                     text,
 "EVENTID"                   text,
 "USER"                      text,
 "RETURN"                    text,
 "EVENTCOUNT"                text,
 "SOURCETYPE"                text,
 "HOSTNAME"                  text
)
SERVER duckdb_server
OPTIONS (
    table 'read_parquet("/var/parquetraw/WinSystem_*.parquet", filename=true)'
);

-- broken iis has duplicate column name "proto"
CREATE FOREIGN TABLE public.iis (
 "EVENTID"                    text,
 "SRCPORT"                    text,
 "MESSAGE"                    text,
 "TABLE"                      text,
 "FWADDR"                     text,
 "CATEGORY"                   text,
 "SRCADDR"                    text,
 "DSTPORT"                    text,
 "PROTO"                      text,
 "DSTADDR"                    text,
 "PRIORITY"                   text,
 "c"                          text,
 "n"                          text,
 "srcInt"                     text,
 "dstInt"                     text,
 "srcMac"                     text,
 "dstMac"                     text,
 "proto"                      text,
 "HOSTNAME"                   text
)
SERVER duckdb_server
OPTIONS (
    table 'read_parquet("/var/parquetraw/iis_*.parquet", filename=true)'
);

-- broken linux has duplicate column name "proto" 
CREATE FOREIGN TABLE public.linux (
 "EVENTID"                    text,
 "SRCPORT"                    text,
 "MESSAGE"                    text,
 "TABLE"                      text,
 "FWADDR"                     text,
 "CATEGORY"                   text,
 "SRCADDR"                    text,
 "DSTPORT"                    text,
 "PROTO"                      text,
 "DSTADDR"                    text,
 "PRIORITY"                   text,
 "c"                          text,
 "n"                          text,
 "srcInt"                     text,
 "dstInt"                     text,
 "srcMac"                     text,
 "dstMac"                     text,
 "proto"                      text,
 "HOSTNAME"                   text
)
SERVER duckdb_server
OPTIONS (
    table 'read_parquet("/var/parquetraw/linux_*.parquet", filename=true)'
);

-- mssql has duplicate column name "proto" 
CREATE FOREIGN TABLE public.mssql (
 "EVENTID"                    text,
 "SRCPORT"                    text,
 "MESSAGE"                    text,
 "TABLE"                      text,
 "FWADDR"                     text,
 "CATEGORY"                   text,
 "SRCADDR"                    text,
 "DSTPORT"                    text,
 "PROTO"                      text,
 "DSTADDR"                    text,
 "PRIORITY"                   text,
 "c"                          text,
 "n"                          text,
 "srcInt"                     text,
 "dstInt"                     text,
 "srcMac"                     text,
 "dstMac"                     text,
 "proto"                      text,
 "HOSTNAME"                   text
)
SERVER duckdb_server
OPTIONS (
    table 'read_parquet("/var/parquetraw/mssql_*.parquet", filename=true)'
);

-- pix has duplicate column name "proto" 
CREATE FOREIGN TABLE public.pix (
 "EVENTID"                    text,
 "SRCPORT"                    text,
 "MESSAGE"                    text,
 "TABLE"                      text,
 "FWADDR"                     text,
 "CATEGORY"                   text,
 "SRCADDR"                    text,
 "DSTPORT"                    text,
 "PROTO"                      text,
 "DSTADDR"                    text,
 "PRIORITY"                   text,
 "c"                          text,
 "n"                          text,
 "srcInt"                     text,
 "dstInt"                     text,
 "srcMac"                     text,
 "dstMac"                     text,
 "proto"                      text,
 "HOSTNAME"                   text
)
SERVER duckdb_server
OPTIONS (
    table 'read_parquet("/var/parquetraw/pix_*.parquet", filename=true)'
);

-- solaris has duplicate column name "proto"
CREATE FOREIGN TABLE public.solaris (
 "EVENTID"                    text,
 "SRCPORT"                    text,
 "MESSAGE"                    text,
 "TABLE"                      text,
 "FWADDR"                     text,
 "CATEGORY"                   text,
 "SRCADDR"                    text,
 "DSTPORT"                    text,
 "PROTO"                      text,
 "DSTADDR"                    text,
 "PRIORITY"                   text,
 "c"                          text,
 "n"                          text,
 "srcInt"                     text,
 "dstInt"                     text,
 "srcMac"                     text,
 "dstMac"                     text,
 "proto"                      text,
 "HOSTNAME"                   text
)
SERVER duckdb_server
OPTIONS (
    table 'read_parquet("/var/parquetraw/solaris_*.parquet", filename=true)'
);

-- syslog has duplicate column name "proto"
CREATE FOREIGN TABLE public.syslog (
 "EVENTID"                    text,
 "SRCPORT"                    text,
 "MESSAGE"                    text,
 "TABLE"                      text,
 "FWADDR"                     text,
 "CATEGORY"                   text,
 "SRCADDR"                    text,
 "DSTPORT"                    text,
 "PROTO"                      text,
 "DSTADDR"                    text,
 "PRIORITY"                   text,
 "c"                          text,
 "n"                          text,
 "srcInt"                     text,
 "dstInt"                     text,
 "srcMac"                     text,
 "dstMac"                     text,
 "proto"                      text,
 "HOSTNAME"                   text
)
SERVER duckdb_server
OPTIONS (
    table 'read_parquet("/var/parquetraw/syslog_*.parquet", filename=true)'
);

-- winapplication has duplicate column name "proto"
CREATE FOREIGN TABLE public.winapplication (
 "EVENTID"                    text,
 "SRCPORT"                    text,
 "MESSAGE"                    text,
 "TABLE"                      text,
 "FWADDR"                     text,
 "CATEGORY"                   text,
 "SRCADDR"                    text,
 "DSTPORT"                    text,
 "PROTO"                      text,
 "DSTADDR"                    text,
 "PRIORITY"                   text,
 "c"                          text,
 "n"                          text,
 "srcInt"                     text,
 "dstInt"                     text,
 "srcMac"                     text,
 "dstMac"                     text,
 "proto"                      text,
 "HOSTNAME"                   text
)
SERVER duckdb_server
OPTIONS (
    table 'read_parquet("/var/parquetraw/winapplication_*.parquet", filename=true)'
);


```

Create user for grafana datasource:
```sql
CREATE USER grafanareader WITH PASSWORD 'password';
GRANT USAGE ON SCHEMA public TO grafanareader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO grafanareader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO grafanareader;
```

test
```bash
PGPASSWORD=password psql -h 127.0.0.1 -U grafanareader postgres

```
then:
```sql
select * from public.aggregations_table limit 10;
```

-----
# Add swap file (need to compile libduckdb only)
```bash
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
```
# Compile
```bash
mkdir libduckdb
cd libduckdb
wget -T 36000 -t 0 --waitretry=5 https://github.com/duckdb/duckdb/releases/download/v0.9.2/libduckdb-src.zip
unzip -n -d . libduckdb-src.zip
clang++ -c -fPIC -std=c++11 -D_GLIBCXX_USE_CXX11_ABI=0 duckdb.cpp -o duckdb.o
clang++ -shared -o libduckdb.so *.o

cp libduckdb.so $(pg_config --libdir)
```

# Links:
- https://dev.to/rainbowhat/postgresql-16-installation-on-ubuntu-2204-51ia
- https://github.com/alitrack/duckdb_fdw/pull/38
- https://github.com/digoal/blog/blob/master/202401/20240124_01.md
