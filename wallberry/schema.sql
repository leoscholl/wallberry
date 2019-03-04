DROP TABLE IF EXISTS sensor;
DROP TABLE IF EXISTS temperature;
DROP TABLE IF EXISTS humidity;
DROP TABLE IF EXISTS pressure;
DROP TABLE IF EXISTS thermostat;

CREATE TABLE sensor (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL
);

CREATE TABLE temperature (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sensor_id INTEGER NOT NULL,
  time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  value REAL,
  FOREIGN KEY (sensor_id) REFERENCES sensor (id)
);

CREATE TABLE humidity (  
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sensor_id INTEGER NOT NULL,
  time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  value INTEGER,
  FOREIGN KEY (sensor_id) REFERENCES sensor (id)
);

CREATE TABLE pressure (  
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sensor_id INTEGER NOT NULL,
  time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  value INTEGER,
  FOREIGN KEY (sensor_id) REFERENCES sensor (id)
);

CREATE TABLE thermostat (
  id INTEGER PRIMARY KEY,
  setting TEXT NOT NULL,
  value NUMERIC
);

CREATE UNIQUE INDEX idx_thermostat_setting ON thermostat (setting);