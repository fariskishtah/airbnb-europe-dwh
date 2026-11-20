-- GOLD: star schema. The whole schema is rebuilt from Silver on every run (deterministic surrogate keys).
-- Grain of fact_offer_observation: ONE offer observation (one row of one source CSV = one city / day-type sample).
-- No Date, Host or Property dimension: the source has no calendar date, no host id, no listing id, no property type.
DROP SCHEMA IF EXISTS gold CASCADE;
CREATE SCHEMA gold;

CREATE TABLE gold.dim_city (
    city_key     smallint PRIMARY KEY,
    city_name    text NOT NULL UNIQUE,
    country      text NOT NULL,            -- reference attribute (public knowledge), not from the source CSVs
    ref_lat      double precision NOT NULL,
    ref_lng      double precision NOT NULL
);
CREATE TABLE gold.dim_day_type (
    day_type_key smallint PRIMARY KEY,
    day_type     text NOT NULL UNIQUE CHECK (day_type IN ('weekday','weekend')),
    source_label text NOT NULL             -- 'weekdays' / 'weekends' as in the file name
);
CREATE TABLE gold.dim_room_type (
    room_type_key smallint PRIMARY KEY,
    room_type     text NOT NULL UNIQUE,
    is_shared     boolean NOT NULL,
    is_private    boolean NOT NULL,
    is_entire     boolean NOT NULL
);
CREATE TABLE gold.dim_host_status (
    host_status_key    smallint PRIMARY KEY,
    is_superhost       boolean NOT NULL,
    multi_listing_host boolean NOT NULL,   -- source column "multi"
    business_host      boolean NOT NULL,   -- source column "biz"
    host_status_label  text NOT NULL,
    UNIQUE (is_superhost, multi_listing_host, business_host)
);
CREATE TABLE gold.dim_source_file (
    source_file_key smallint PRIMARY KEY,
    source_file     text NOT NULL UNIQUE,
    city_key        smallint NOT NULL REFERENCES gold.dim_city(city_key),
    day_type_key    smallint NOT NULL REFERENCES gold.dim_day_type(day_type_key),
    sha256          text NOT NULL,
    md5_verified    boolean,
    size_bytes      bigint NOT NULL,
    source_row_count integer NOT NULL,
    UNIQUE (city_key, day_type_key)
);
CREATE TABLE gold.fact_offer_observation (
    offer_key                  integer PRIMARY KEY,
    offer_id                   text NOT NULL UNIQUE,
    city_key                   smallint NOT NULL REFERENCES gold.dim_city(city_key),
    day_type_key               smallint NOT NULL REFERENCES gold.dim_day_type(day_type_key),
    room_type_key              smallint NOT NULL REFERENCES gold.dim_room_type(room_type_key),
    host_status_key            smallint NOT NULL REFERENCES gold.dim_host_status(host_status_key),
    source_file_key            smallint NOT NULL REFERENCES gold.dim_source_file(source_file_key),
    source_row_index           integer NOT NULL,
    two_night_total_eur        double precision NOT NULL CHECK (two_night_total_eur > 0),
    nightly_equivalent_eur     double precision NOT NULL CHECK (nightly_equivalent_eur > 0),
    person_capacity            smallint NOT NULL CHECK (person_capacity >= 1),
    bedrooms                   smallint NOT NULL CHECK (bedrooms >= 0),
    cleanliness_rating         double precision NOT NULL CHECK (cleanliness_rating BETWEEN 0 AND 10),
    guest_satisfaction_overall double precision NOT NULL CHECK (guest_satisfaction_overall BETWEEN 0 AND 100),
    dist_city_center_km        double precision NOT NULL CHECK (dist_city_center_km >= 0),
    dist_metro_km              double precision NOT NULL CHECK (dist_metro_km >= 0),
    attr_index                 double precision NOT NULL,
    attr_index_norm            double precision NOT NULL,
    rest_index                 double precision NOT NULL,
    rest_index_norm            double precision NOT NULL,
    lat                        double precision NOT NULL CHECK (lat BETWEEN -90 AND 90),
    lng                        double precision NOT NULL CHECK (lng BETWEEN -180 AND 180),
    is_studio                  boolean NOT NULL,
    price_outlier_iqr          boolean NOT NULL,
    UNIQUE (source_file_key, source_row_index)
);
CREATE INDEX ix_fact_city      ON gold.fact_offer_observation(city_key);
CREATE INDEX ix_fact_day       ON gold.fact_offer_observation(day_type_key);
CREATE INDEX ix_fact_room      ON gold.fact_offer_observation(room_type_key);
CREATE INDEX ix_fact_host      ON gold.fact_offer_observation(host_status_key);
CREATE INDEX ix_fact_price     ON gold.fact_offer_observation(two_night_total_eur);
CREATE INDEX ix_fact_city_day  ON gold.fact_offer_observation(city_key, day_type_key);
