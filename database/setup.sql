create table IF NOT EXISTS project (
  name text, 
  description  text,
  useMTurk integer,
  MTurkDetail  text,
  sklearnMode  text,
  sklearnDetail  text,
  functions  text,
  has_changes  integer DEFAULT 0,
  sample_predict  text,
  primary key     (name)
);
