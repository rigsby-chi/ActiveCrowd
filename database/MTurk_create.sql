create table IF NOT EXISTS "{0}_records" (
  success_id  integer,
  raw_data  text,
  data    text,
  hitid    varchar(30),
  hittypeid  varchar(30),
  reward  float,
  creation_time  timestamp,
  answer    text,
  accept_time  timestamp,
  submit_time  timestamp,
  is_expired  boolean DEFAULT false,
  primary key     (success_id)
);
                        
create table IF NOT EXISTS "{0}_failure" (
  failure_id  serial,
  raw_data  text,
  data    text,
  message    text,
  primary key     (failure_id)
);

create table IF NOT EXISTS "{0}_pending" (
  success_id  serial,
  raw_data  text,
  data    text,
  hitid    varchar(30),
  hittypeid  varchar(30),
  primary key     (hitid)
);

create table IF NOT EXISTS "{0}_answers" (
  raw_data  text,
  answer    text,
  hidid     text
);
