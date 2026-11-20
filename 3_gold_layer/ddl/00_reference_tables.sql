-- Reference (public-knowledge) attributes used by DimCity. Loaded by the gold builder from airbnb_dwh/reference.py.
CREATE SCHEMA IF NOT EXISTS gold_ref;
CREATE TABLE IF NOT EXISTS gold_ref.city_reference (
    city text PRIMARY KEY, display_name text NOT NULL, country text NOT NULL, lat double precision NOT NULL, lng double precision NOT NULL);
