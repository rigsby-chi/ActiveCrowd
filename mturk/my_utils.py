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
  """Load and execute sql from local file
  
  Args:
      sql_file: A string of the path to the sql file
      dbname: A string of the name of target database
  """
  some_options = "-X -q  -1 -v ON_ERROR_STOP=0 --pset pager=off"

  run_cmd("/usr/bin/psql {0} -d {1} -f {2}".format(some_options, dbname, sql_file))

def run_cmd(cmd):
  """Execute a terminal command
  
  Args:
      cmd: A string of the command
      
  Returns:
      A string of the message returned by terminal
  """
  print cmd
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

  return cmd_out

def get_db_connection(db, db_user, db_password):
  """Get a database connection
  
  Args:
      db: A string of the name of target database
      db_user: A string of the database user name
      db_password: A string of the database user password
      
  Returns:
      An database connection object
  """
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
  """Enable logging of exeuctions
  
  Attributes:
      db_conn: A database connection object
      project: A string of the project name
  """
  db_conn = None
  project = None
  
  def __init__(self, project, db=None, db_user=None, db_password=None):
    """Initialization of logger object
    
    Args:
        project: A string of the project name
        db: A string of the name of the target database
        db_user: A string of the database user name
        db_password: A stirng of the database user passowrd
    """
    self.project = project
    if db is not None and db_user is not None and db_password is not None:
      self.db_conn = get_db_connection(db, db_user, db_password)
    self.log('info', 'Logger is created')
    
  def log(self, msg_type, message):
    """Log a message
    
    Args:
        msg_type: A string of the type of message. Could be either of info, success, danger and warning
        message: A string of the content of the message
    """
    if not self.db_conn is None:
      cur = self.db_conn.cursor()
      cur.execute('''INSERT INTO "{0}_logs" (time, type, message) VALUES (CURRENT_TIMESTAMP, %s, %s)'''.format(self.project), (msg_type, message,))
      self.db_conn.commit()
    print '[' + msg_type + '] ' + message
      
class Recorder(object):
  """Enable recording of important events or the project stage at a moment
  
  Attributes:
      db_conn: A database connection object
      project: A string of the project name
  """
  db_conn = None
  project = None
  
  def __init__(self, project, db=None, db_user=None, db_password=None):
    """Initialization of recorder object
    
    Args:
        project: A string of the project name
        db: A string of the name of the target database
        db_user: A string of the database user name
        db_password: A stirng of the database user passowrd
    """
    self.project = project
    if db is not None and db_user is not None and db_password is not None:
      self.db_conn = get_db_connection(db, db_user, db_password)
    
  def record(self, recordType, useSandbox = 'NULL', stopAtErrorRate = 'NULL', stopAtLabeledSamples = 'NULL', sklearnSetting = 'NULL', controlGroupSize = 'NULL', controlGroupAccuracy = 'NULL', kFoldAccuracy = 'NULL', deviation = 'NULL', labeledAmount = 'NULL', payment = 'NULL'):
    """Record an event or a stage
    
    Args:
        recordType: A string of the type of record picked up by handler
        useSandbox: A string indicating whether the events happened with sandbox enabled
        stopAtErrorRate: An integer (or 'NULL') of the stopping error rate
        stopAtLabeledSamples: An integer (or 'NULL') of the stopping labeled sample amount
        sklearnSetting: A string of the sklearn setting
        controlGroupSize: An integer (or 'NULL') of the current control group size
        controlGroupAccuracy: A float of the current control group validation accuracy
        kFoldAccuracy: A float of the current k fold validation accuracy
        deviation: A float of the deviation of the current k fold validation accuracy
        labeledAmount: An integer of the current labeled sample amount
        payment: A float of the current total payment
    """
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
  """Exit execution with an error record
  
  Args:
      recorder: A recorder object
  """
  recorder.record(recordType='finishWithError')
  sys.exit()
