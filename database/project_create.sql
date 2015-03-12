create table IF NOT EXISTS "{0}_samples" (
  sample_id serial, 
  sample  text,
  feature text,
  label  text,
  label_source  text,
  for_testing  boolean DEFAULT false, 
  primary key     (sample_id)
);

create table IF NOT EXISTS "{0}_logs" (
  log_id serial, 
  time  timestamp,
  type  text,
  message text,
  primary key     (log_id)
);

create table IF NOT EXISTS "{0}_learning_records" (
  record_id serial, 
  time  timestamp,
  record_type  text,
  use_sandbox  integer,
  stop_at_error_rate  float,
  stop_at_labeled_samples  integer,
  sklearn_setting  text,
  control_group_size  integer,
  control_group_accuracy  float,
  k_fold_accuracy  float,
  deviation  float,
  labeled_amount  integer,
  payment  float,
  primary key     (record_id)
);
