-- Bronze (raw, all TEXT, exactly as in the CSV files) and Silver (typed, cleaned) staging tables.
-- Idempotent: safe to re-run; Bronze content is only replaced per file when the file hash changes.
CREATE SCHEMA IF NOT EXISTS meta;
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;

CREATE TABLE IF NOT EXISTS bronze.ingestion_log (
    source_file     text PRIMARY KEY,
    city            text NOT NULL,
    day_type        text NOT NULL,
    sha256          text NOT NULL UNIQUE,         -- UNIQUE => the same file content cannot be ingested twice
    md5             text NOT NULL,
    zenodo_md5      text,
    md5_verified    boolean,
    size_bytes      bigint NOT NULL,
    row_count       integer NOT NULL,
    column_count    integer NOT NULL,
    ingested_at     timestamptz NOT NULL DEFAULT now(),
    run_id          text NOT NULL
);

CREATE TABLE IF NOT EXISTS bronze.raw_offers (
    source_file        text    NOT NULL REFERENCES bronze.ingestion_log(source_file) ON DELETE CASCADE,
    source_row_number  integer NOT NULL,            -- 1-based data-row ordinal inside the source file
    source_row_index   text,                        -- the unnamed exported index column, verbatim
    realsum text, room_type text, room_shared text, room_private text, person_capacity text,
    host_is_superhost text, multi text, biz text, cleanliness_rating text, guest_satisfaction_overall text,
    bedrooms text, dist text, metro_dist text, attr_index text, attr_index_norm text,
    rest_index text, rest_index_norm text, lng text, lat text,
    PRIMARY KEY (source_file, source_row_number)
);

CREATE TABLE IF NOT EXISTS silver.airbnb_europe_master (
    offer_id                   text PRIMARY KEY,
    source_file                text NOT NULL,
    source_row_index           integer NOT NULL,
    city                       text NOT NULL,
    day_type                   text NOT NULL,
    real_sum                   double precision NOT NULL,
    two_night_total_eur        double precision NOT NULL,
    nightly_equivalent_eur     double precision NOT NULL,
    room_type                  text NOT NULL,
    room_shared                boolean NOT NULL,
    room_private               boolean NOT NULL,
    person_capacity            smallint NOT NULL,
    host_is_superhost          boolean NOT NULL,
    multi_listing_host         boolean NOT NULL,
    business_host              boolean NOT NULL,
    cleanliness_rating         double precision NOT NULL,
    guest_satisfaction_overall double precision NOT NULL,
    bedrooms                   smallint NOT NULL,
    dist_city_center_km        double precision NOT NULL,
    dist_metro_km              double precision NOT NULL,
    attr_index                 double precision NOT NULL,
    attr_index_norm            double precision NOT NULL,
    rest_index                 double precision NOT NULL,
    rest_index_norm            double precision NOT NULL,
    lng                        double precision NOT NULL,
    lat                        double precision NOT NULL,
    is_studio                  boolean NOT NULL,
    price_outlier_iqr          boolean NOT NULL,
    UNIQUE (source_file, source_row_index)
);
