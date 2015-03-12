import subprocess, sys, os, traceback, psycopg2
from optparse import OptionParser

def parse(option_dict):
  option_parser = OptionParser()

  for opt_name, default_val in option_dict.iteritems():
    try:
      default_val,comment = default_val
    except:
      comment = opt_name
      pass

    option_parser.add_option(
      "--"+opt_name,
      type=type(default_val), dest=opt_name,
      default=default_val,
      help=comment, metavar="#"+opt_name.upper())

  options,args = option_parser.parse_args()
  return dict(vars(options).items())

def load_sql(sql_file, dbname):
  some_options = "-X -q  -1 -v ON_ERROR_STOP=0 --pset pager=off"

  run_cmd("/usr/bin/psql {0} -d {1} -f {2}".format(some_options, dbname, sql_file))

def run_cmd(cmd):
  print cmd
  #ret= subprocess.Popen(cmd, shell=True,
  #                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.read()
  #return ret
  ret = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  cmd_out = ''
  while True:
    out = ret.stdout.read(1)
    cmd_out = cmd_out + out
    if out == '' and ret.poll() != None:
      break
    if out != '':
      sys.stdout.write(out)
      sys.stdout.flush()

  #print cmd_out
  return cmd_out

def parse_conf(conf_fn):
  with open(conf_fn, 'r') as ifp:
    configs = eval(ifp.read())

  if not isinstance(configs['resources'], dict):
    with open(configs['resources'], 'r') as ifp:
      configs['resources'] = eval(ifp.read())

  if not isinstance(configs['generators'], dict):
    with open(configs['generators'], 'r') as ifp:
      configs['generators'] = eval(ifp.read())

  return configs

#Get a database connection object
def get_db_connection(db, db_user, db_password):
  try:
    conn_details = "dbname='{0}' ".format(db) + \
                   "user='{0}' ".format(db_user) + \
                   "password='{0}'".format(db_password)
    conn = psycopg2.connect(conn_details)
    return conn
  except:
    print "[Error] Unable to connect to the database"
    traceback.print_exc()
    sys.exit()

class Logger(object):
  db_conn = None
  project = None
  
  def __init__(self, project, db=None, db_user=None, db_password=None):
    self.project = project
    if db is not None and db_user is not None and db_password is not None:
      self.db_conn = get_db_connection(db, db_user, db_password)
    self.log('info', 'Logger is created')
    
  def log(self, msg_type, message):
    if not self.db_conn is None:
      cur = self.db_conn.cursor()
      cur.execute('''INSERT INTO "{0}_logs" (time, type, message) VALUES (CURRENT_TIMESTAMP, %s, %s)'''.format(self.project), (msg_type, message,))
      self.db_conn.commit()
    print '[' + msg_type + '] ' + message
      
class Recorder(object):
  db_conn = None
  project = None
  
  def __init__(self, project, db=None, db_user=None, db_password=None):
    self.project = project
    if db is not None and db_user is not None and db_password is not None:
      self.db_conn = get_db_connection(db, db_user, db_password)
    
  def record(self, recordType, useSandbox = 'NULL', stopAtErrorRate = 'NULL', stopAtLabeledSamples = 'NULL', sklearnSetting = 'NULL', controlGroupSize = 'NULL', controlGroupAccuracy = 'NULL', kFoldAccuracy = 'NULL', deviation = 'NULL', labeledAmount = 'NULL', payment = 'NULL'):
    if stopAtErrorRate is None:
      stopAtErrorRate = 'NULL'
    if not self.db_conn is None:
      try:
        cur = self.db_conn.cursor()
        cur.execute("""INSERT INTO "{0}_learning_records" (time, record_type, use_sandbox, stop_at_error_rate, stop_at_labeled_samples, sklearn_setting, control_group_size, control_group_accuracy, k_fold_accuracy, deviation, labeled_amount, payment) VALUES (CURRENT_TIMESTAMP, '{1}', {2}, {3}, {4}, %s, {5}, {6}, {7}, {8}, {9}, {10})""".format(self.project, recordType, useSandbox, stopAtErrorRate, stopAtLabeledSamples, controlGroupSize, controlGroupAccuracy, kFoldAccuracy, deviation, labeledAmount, payment), (str(sklearnSetting), ))
        self.db_conn.commit()
      except Exception, e:
        traceback.print_exc()
        
def exit(recorder):
  recorder.record(recordType='finishWithError')
  sys.exit()
