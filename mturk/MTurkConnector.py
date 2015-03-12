import my_utils
import os, sys, glob, traceback
import fileinput, csv, json
import psycopg2
from time import sleep

class MTurkConnector(object):
  """Enable communication to MTurk server
  
  Learning automation coordinate machine learning object (classifier - clf) and 
  MTurkConnector instance (mc) to achieve automated active learning. 
  
  Attributes:
      param_dict: A dict storing MTurk connection configuration
      param_dict['clt_path']: A string of the path to the MTurk Command Line Tool
      param_dict['clt_bin']: A string of the path to the MTurk Command Line Tool's
                             bin folder
      param_dict['root_path']: A string of the root path of the project
      param_dict['aws_key']: A string of the AWS key
      param_dict['aws_secret_key']: A string of the AWS secret key
      param_dict['rootkey']: A string of the path to the CSV file storing the keys
      param_dict['use_sandbox']: A string of whether to use sandbox mode. 'true' for
                                 using sandbox and 'false' for not using sandbox
      param_dict['project']: A string of the project name
      param_dict['project_path']: A string of the project path
      param_dict['q_path']: A string of path to the question file
      param_dict['p_path']: A string of path to the properties file
      param_dict['db']: A string of the database name
      param_dict['db_user']: A string of the database user name
      param_dict['db_password']: A string of the database user password
      logger: A logger object to perform logging operation
  """
  param_dict = {
    'clt_path'            : 'mturk/aws-mturk-clt-1.3.1',
    'clt_bin'             : 'mturk/aws-mturk-clt-1.3.1/bin/',
    'root_path'           : '',
    'aws_key'             : '',
    'aws_secret_key'      : '',
    'rootkey'             : '',
    'use_sandbox'         : 'true',
    'project'             : '',
    'project_path'        : '',
    'q_path'              : '',
    'p_path'              : '',
    'db'                  : '',
    'db_user'             : '',
    'db_password'         : ''
  }
  
  logger = None
  
  
  def __init__(self, project, db, db_user, db_password, root_path = '', \
               root_key_path = None, aws_key = None, \
               aws_secret_key = None, use_sandbox = True, logger = None):
    """Initialize a MTurkConnector object
    
    Initialization opertion of a MTurkConnector object. It includes fixing MTurk 
    Command Line Tool configuration file, fixing ssl connection address, setting 
    sandbox mode, setting project and relative file paths, and checking MTurk data
    files and directories.
    
    Args:
        project: A string of the project name
        db: A string of the database name
        db_user: A string of the database user name
        db_password: A string of the database user password
        root_path: A string of the path to the project folder
        root_key_path: A string of the path to the CSV file storing the keys
        aws_key: A string of the AWS key used to identify MTurk account
        aws_secret_key: A string of the AWS secret key used to verify MTurk account
        use_sandbox : A boolean of whether to use sandbox mode or not
        logger: A logger object to perform logging operation
    """
    self.logger = logger
    if self.logger is None:
      self.logger = my_utils.Logger(project)
    self.param_dict = my_utils.parse(self.param_dict)
    self.param_dict['clt_bin'] = self.param_dict['clt_path'] + "/bin/"
    self.param_dict['root_path'] = root_path
    self.param_dict['project'] = project
    self.param_dict['project_path'] = self.param_dict['root_path']+ '/' + project \
                                      if not self.param_dict['root_path'] == '' else 'project/' + project
    self.param_dict['use_sandbox'] = 'true' if use_sandbox else 'false'
    self.param_dict['db'] = db
    self.param_dict['db_user'] = db_user
    self.param_dict['db_password'] = db_password

    #Read aws key and aws secret key from rootkey file
    if root_key_path is not None:
      self.param_dict['rootkey'] = root_key_path
      
    if self.param_dict['rootkey'] is not "":
      try:
        rootkeyFile = open(self.param_dict['rootkey'])
        aws_access = rootkeyFile.readlines()
        self.param_dict['aws_key'] = aws_access[0].split("=")[1].split("\r")[0]
        self.param_dict['aws_secret_key'] = aws_access[1].split("=")[1]
        rootkeyFile.close()
      except:
        self.logger.log('danger', '[Error] Fail to load rootkey from ' + self.param_dict['rootkey'])
        sys.exit()

    elif not aws_key == None and not aws_secret_key == None:
      self.param_dict['aws_key'] = aws_key
      self.param_dict['aws_secret_key'] = aws_secret_key

    #Set key to mturk command line configuration file
    if self.param_dict['aws_key'] is not "" and \
       self.param_dict['aws_secret_key'] is not "":
      self.set_clt_access(key=self.param_dict['aws_key'], \
      skey=self.param_dict['aws_secret_key'])
    else:
      self.logger.log('danger', 'Missing AWS Secret Key or AWS Access Key ID')
      sys.exit()
      
    self.fix_service_url()
    self.fix_properties_file_not_found()
    
    #create necessary directory
    if not os.path.exists(self.param_dict['project_path']):
      os.makedirs(self.param_dict['project_path'])

    #create tables for the project
    self.create_tables()
      
  def set_question_file(self, question_file=None):
    """Load question file
    
    Args:
      question_file: A string of path to the location of question file
    """
    if not question_file == None and os.path.exists(question_file):
      self.param_dict['q_path'] = question_file
      self.logger.log('success', 'Question file is loaded')
    else:
      self.logger.log('danger', 'Question file not found.')
      sys.exit()

  def set_properties_file(self, properties_file=None):
    """Load properties file
    
    Args:
      properties_file: A string of path to the location of question file
    """
    if not properties_file == None and os.path.exists(properties_file):
      self.param_dict['p_path'] = properties_file
      self.logger.log('success', 'Properties file is loaded')
    else:
      self.logger.log('danger', 'Properties file not found.')
      sys.exit()

  def get_pending_amount(self):
    """Get the amount of HITs pending for answers
    
    Get the amount of HITs pending for answers, which is the number 
    of rows remain in the pending table.
    
    Returns:
        An integer of the amount of HITs pending for answers
    """
    conn = self.get_db_connection()
    cur = conn.cursor()
    cur.execute('''SELECT count(*) FROM "{0}"'''.format(self.param_dict['project'] + '_pending'))
    rows = cur.fetchall()
    conn.close()
    return int(rows[0][0])

  def get_total_payment(self):
    """Get total payment made for all answered HITs
    
    Get total payment made for all answered HITs, which is calculated 
    by querying the record table for all records of all answered HITs 
    and summing up their reward.
    
    Returns:
        A float of the total payment made for all answered HITs
    """
    conn = self.get_db_connection()
    cur = conn.cursor()
    cur.execute('''SELECT sum(reward) FROM "{0}"'''.format(self.param_dict['project'] + '_records'))
    rows = cur.fetchall()
    conn.close()
    if not rows is None and not rows[0][0] is None:
      return float(rows[0][0])
    else:
      return 0

  def get_balance(self):
    """Get the current balance of the MTurk account
    
    Returns:
        A string retured by MTurk Command Line Tool indicating the
        current balance
    """
    cmd = self.set_cmd("getBalance")
    return my_utils.run_cmd(cmd)

  def upload_hits(self, header, real_data_lists, display_data_lists):
    """Upload HITs to MTurk server
    
    Upload formated inforamtion to MTurk server to create new HITs. It 
    requires a question file and properties file in place and it will 
    generate an .input file and for HIT contents, and a .success file
    storing the information of successfully created HITs (and a .failure 
    file if any of HITs is failed to be created).
    
    Args:
        header: A list of string indicating the placeholder name in the question 
                file. For example, if the question file have placeholder ${value}, 
                the header list should have 'value' stored. This list can be 
                automatically generate using get_auto_header() method
        real_data_lists: A list of lists of objects storing what a HIT question stand
                         for. Inner lists should have length same as the amount of 
                         questions while the outer list should have length same as the
                         amount of HITs to be created. For example, if the question 
                         file defines 3 question in a HIT and 2 HITs are going to be 
                         created, then this list should be something like [[HIT1Q1, 
                         HIT1Q2, HIT1Q3], [HIT2Q1, HIT2Q2, HIT3Q3]] where HIT<n>Q<m> 
                         are something that used to associate the question to where it 
                         is used, such as the IDs of records in database
        data_lists: A list of lists of data going to be upload to mturk to replace the 
                    placeholders in questions specified in the question file. Inner lists 
                    should have length same as the amount of placeholders in the quesiton 
                    file while the outer list should have length same as the amount of 
                    HITs to be created. For example, if the question file has 3 placeholders
                    and 2 HITs are going to be created, then this list should be something 
                    like [[HIT1V1, HIT1V2, HIT1V3], [HIT2V1, HIT2V2, HIT2V3]] where HIT<n>V<m> 
                    are the value that used in the n-th HIT to replace the placeholder 
                    with name same as the m-th value in header list 
    Returns:
        In integer of the amount of successfully created HITs
    """
    project = self.param_dict['project']
    label = self.param_dict['project_path'] + '/tmp'
    input_path = self.param_dict['project_path'] + '/tmp.input'
    q_path = self.param_dict['q_path']
    p_path = self.param_dict['p_path']
    
    #Ensure question file and properties files are in place
    if not os.path.exists(q_path):
      self.logger.log('danger', 'Question file not found.')
      sys.exit()
    if not os.path.exists(p_path):
      self.logger.log('danger', 'Properties file not found.')
      sys.exit()

    #Create input file
    self.logger.log('info', 'Creating .input file...')
    with open(input_path, 'wb') as input_file:
      csv_writer = csv.writer(input_file, delimiter='\t')
      csv_writer.writerow(header)
      for data in display_data_lists:
        csv_writer.writerow(data)

    #Upload hits to mturk server
    cmd_results = self.load_hits(input_path, q_path, p_path, label)

    conn = self.get_db_connection()
    cur = conn.cursor()

    #Record failed data
    failure = []
    failure_msg = []
    if "[ERROR] Error creating HIT " in cmd_results:
      cmd_results = cmd_results.split('\n')
      for line in cmd_results:
        if "[ERROR] Error creating HIT " in line:
          hit_number = int(line.split("[ERROR] Error creating HIT ")[1].split(" (")[0]) - 1
          failure.append(hit_number)
          failure_msg.append(line)
          #Insert failure record in database
          try:
            cur.execute("""INSERT INTO {0}""".format('"' + project + '_failure"') + \
                        """(raw_data,data,message) VALUES (%s,%s,%s)""", 
                        (str(real_data_lists[hit_number]), str(display_data_lists[hit_number]), line))
            conn.commit()
            self.logger.log('warning', 'Fail to create HIT: ' + line)
          except:
            self.logger.log('warning', 'Error occurs during insertion of a failure record.')
            conn.rollback()

    #Record success data
    HITs = []
    with open(label + '.success', 'rb') as success_file:
      reader = csv.reader(success_file, delimiter='\t')
      next(reader, None)
      for row in reader:
        HITs.append([row[0], row[1]])

    loaded_display_data = []
    loaded_real_data = []
    for i in range (0, len(display_data_lists)):
      if not i in failure:
        loaded_display_data.append(display_data_lists[i])
        loaded_real_data.append(real_data_lists[i])
    
    #Insert successfully created HITs into pending table
    for i in range (0, len(HITs)):
      try:
        cur.execute("""INSERT INTO {0}""".format('"' + project + '_pending"') + \
                    """(raw_data,data,hitid,hittypeid) VALUES (%s,%s,%s,%s)""", 
                    (str(loaded_real_data[i]), str(loaded_display_data[i]), HITs[i][0], HITs[i][1]))
        conn.commit()
        self.logger.log('info', 'HIT [' + HITs[i][0] + '] has been created for samples: ' + str(loaded_real_data[i]))
      except:
        self.logger.log('warning', 'Error occurs during insertion of a pending record.')
        self.logger.log('warning', 'HIT [' + HITs[i][0] + '] has not been insert into pending list.')
        conn.rollback()
        
    cur.close()
    conn.close()
    
    #Info user if any HIT is failed to be created
    if(len(failure) > 0):
      self.logger.log('warning', str(len(failure)) + ' HITs failed to be created.')
      for msg in failure_msg:
        self.logger.log('warning', msg)
        
    #Print the URL address of created HITs
    if(len(HITs) > 0):
      link = 'https://workersandbox.mturk.com/mturk/preview?groupId=' + HITs[0][1]
      self.logger.log('success', str(len(HITs)) + ' HITs have been created successfully. You may see them on: <a target="_blank" href="' + link + '">' + link + '</a>')
    elif(len(HITs) == 0):
      self.logger.log('danger', 'No HIT could be created. Please read the logs for more details.')
      raise Exception('No HIT could be created. Please read the logs for more details.')
    return len(HITs)

  def update_results(self):
    """Query MTurk server and retrieve answers
    
    Query MTurk server and retrieve answers. Answered HITs will be removed 
    from pending table and but added to record table. Also, a copy of answers
    and their corresponding real_data_lists (provided in upload_hits method)
    will be inserted to answer table for other process to pick up and use.
    
    Returns:
        An integer of the amount of answered and retrieved HITs
    """
    project = self.param_dict['project']
    label = self.param_dict['project_path'] + '/tmp'
    s_path = self.param_dict['project_path'] + '/tmp.success'
    r_path = self.param_dict['project_path'] + '/tmp.results'
    
    conn = self.get_db_connection()
    cur = conn.cursor()
    
    #Get all pending hits details
    self.logger.log('info', 'Retrieving pending HIT list...')
    try:
      cur.execute('''SELECT * FROM "{0}_pending"'''.format(project))
      pending_list = cur.fetchall()
      total_rows = len(pending_list)
    except Exception, e:
      self.logger.log('warning', 'Fail to retrieve pending HIT details from database.' + e.message)
      return 0
      
    self.logger.log('info', 'There are ' + str(total_rows) + ' HITs pending for updates.')
    if total_rows == 0:
      return 0   

    #Create .success file for MTurk command line tool
    with open(s_path, 'wb') as success_file:
      csv_writer = csv.writer(success_file, delimiter='\t')
      csv_writer.writerow(['hitid', 'hittypeid'])
      for row in pending_list:
        csv_writer.writerow([row[3], row[4]])

    self.get_results(label)
    self.logger.log('info', 'Parsing response...')
    count = total_rows #Count how many rows left in pending table
    expired_count = 0
    answered_count = 0
    with open(r_path, 'r') as results_file:
      csv_reader = csv.reader(results_file, delimiter='\t')
      header = csv_reader.next()
      num_of_ans = len(header) - 29
      for i in range(0, total_rows):
        row = csv_reader.next()
        answers = []
        for j in range (0,num_of_ans):
          answers.append(row[29+j])
        #If the hit is expired
        if row[11] == 'Reviewable' and sum(answer=='' for answer in answers)==num_of_ans:
          try:
            #Record the hit details
            cur.execute("""INSERT INTO {0}""".format('"' + project + '_records"') + \
                        """(success_id, raw_data, data, hitid, hittypeid, creation_time, """ + \
                        """is_expired) VALUES (%s, %s, %s, %s, %s, %s, true) """, \
                        (pending_list[i][0], pending_list[i][1], pending_list[i][2], \
                        pending_list[i][3], pending_list[i][4], row[6]))
            #Remove from pending list
            cur.execute("""DELETE FROM {0}""".format('"' + project + '_pending"') + \
                        """WHERE hitid=%s""", (pending_list[i][3],))
            self.logger.log('warning', "HIT [" + row[0] + "] is expired")
            expired_count = expired_count + 1
            conn.commit()
            count = count - 1
          except:
            self.logger.log('warning', "Fail to record an expired hit or remove from pending list: " + pending_list[i][3])
            conn.rollback()
        #If the hit is answered
        elif row[11] == 'Reviewable':
          try:
            print row[5][1:]
            #Record the hit details
            cur.execute("""INSERT INTO {0}""".format('"' + project + '_records"') + \
                        """(success_id, raw_data, data, hitid, hittypeid, reward, """ + \
                        """creation_time, answer, accept_time, submit_time) VALUES """ + \
                        """(%s, %s, %s, %s, %s, {0}, %s, %s, %s, %s) """.format(row[5][1:]), \
                        (pending_list[i][0], pending_list[i][1], pending_list[i][2], \
                        pending_list[i][3], pending_list[i][4], row[6], str(answers), row[22], row[23]))
            #Insert to answer pool for client process to retrieve
            cur.execute("""INSERT INTO {0}""".format('"' + project + '_answers"') + \
                        """(raw_data, answer, hidid) VALUES (%s, %s, %s)"""
                        , (pending_list[i][1], str(answers), pending_list[i][3], ))
            #Remove from pending list
            cur.execute("""DELETE FROM {0}""".format('"' + project + '_pending"') + \
                        """WHERE hitid=%s""", (pending_list[i][3],))
            self.logger.log('success', "HIT [" + row[0] + "] is anwsered")
            answered_count = answered_count + 1
            conn.commit()
            count = count - 1
          except:
            self.logger.log('warning', "Error occur during retieve results from an answered HIT" + pending_list[i][3])
            traceback.print_exc()
            conn.rollback()
    
    cur.close()
    conn.close()
    if expired_count > 0:
      self.logger.log('warning', str(expired_count) + ' are expired.')
    if answered_count > 0:
      self.logger.log('success', str(answered_count) + ' HITs are answered.')
    else:
      self.logger.log('warning', str(answered_count) + ' No HIT is answered.')
    self.logger.log('info', str(count) + ' HITs are still pending for answers.')
    return count

  #Get results from answer pool
  def get_answer(self):
    project = self.param_dict['project']
    conn = self.get_db_connection()
    cur = conn.cursor()
    
    try:
      cur.execute("""SELECT * FROM {0}""".format('"' + project + '_answers"'))
      answer_list = cur.fetchall()
      
      if len(answer_list) == 0:
        return None

      new_results = []
      for row in answer_list:
        new_results.append([row[0], row[1], row[2]])
      
      cur.execute("""DELETE FROM {0}""".format('"' + project + '_answers"'))
      conn.commit()
      cur.close()
      conn.close()
    except Exception, e:
      self.logger.log('warning', 'Fail to get result from answer list.' + e.message)
      conn.rollback()
      cur.close()
      conn.close()
      
      
    return new_results

  #Reset account by removing all hits (auto approve), slow command line version, default
  def reset_account(self):
    project = self.param_dict['project']
    
    #Remove all from in mturk server. (auto approve)
    cmd = self.set_cmd("resetAccount")
    cmd = cmd + ' -force'
    result = my_utils.run_cmd(cmd)
    
    conn = self.get_db_connection()
    cur = conn.cursor()
    try:
      cur.execute("""DELETE FROM {0}""".format('"' + project + '_pending"'))
      conn.commit()
    except:
      self.logger.log('warning', 'Fail to reset the account.')
      conn.rollback()
    finally:
      cur.close()
      conn.close()
    
    return result
  
  #Get results and store in .results file
  def get_results(self, label):
    self.logger.log('info', 'Querying MTurk server for HIT status...')
    if not os.path.isfile(label + '.success'):
      print "File " + label + '.success not found'
      return
    cmd = self.set_cmd("getResults")
    cmd = cmd + ' -successfile ' + '"' + label + '.success' + '"'
    cmd = cmd + ' -outputfile ' + '"' + label + '.results' + '"'
    return my_utils.run_cmd(cmd)

  #Set access key and secret key to clt properties file
  def set_clt_access(self, key, skey):
    try:
      properties_file = self.param_dict['clt_bin'] + "mturk.properties"
      for line in fileinput.input(properties_file, inplace=True):
        if "access_key=" in line and "# access_key=" not in line:
          line = "access_key=" + key + '\n'
        elif "secret_key=" in line and "# secret_key=" not in line:
          line = "secret_key=" + skey + '\n'
        sys.stdout.write(line)
      self.logger.log('success', 'MTurk access configuration completed.')
    except Exception, e:
      self.logger.log('warning', 'MTurk access configuration failed. ' + e.message)
      sys.exit()

  #Fix the MTurk command line tool ssl error
  def fix_service_url(self):
    try:
      properties_file = self.param_dict['clt_bin'] + "mturk.properties"
      for line in fileinput.input(properties_file, inplace=True):
        if "service_url=http:" in line:
          line = line.replace("service_url=http:", "service_url=https:")
        sys.stdout.write(line)
      self.logger.log('success', 'MTurk service url parameter is fixed.')
    except Exception, e:
      self.logger.log('warning', 'Fail to fix MTurk service url parameter. ' + e.message)
      sys.exit()

  #Fix the MTurk command line configuration file not found error
  def fix_properties_file_not_found(self):
    properties_file = self.param_dict['clt_bin'] + "mturk.properties"
    my_utils.run_cmd("cp " + properties_file + " ./")

  #set cmd for mturk command line tool
  def set_cmd(self, operation):
    command = self.param_dict['clt_bin'] + operation + '.sh'
    if self.param_dict['use_sandbox'] == 'false':
      return command
    else:
      return command + " -sandbox"
  
  #load hits to mturk according to give question file, input file and properties file
  def load_hits(self, input_path, question_path, properties_path, label):
    self.logger.log('info', 'Start HIT creation process.')
    cmd = self.set_cmd("loadHITs")
    cmd = cmd + ' -input ' + '"' + input_path + '"'
    cmd = cmd + ' -question ' + '"' + question_path + '"'
    cmd = cmd + ' -properties ' + '"' + properties_path + '"'
    cmd = cmd + ' -label ' + '"' + label + '"'
    return my_utils.run_cmd(cmd)

  #Get a database connection object
  def get_db_connection(self):
    return my_utils.get_db_connection(self.param_dict['db'], self.param_dict['db_user'], self.param_dict['db_password'])
  
  #Create tables for the project
  def create_tables(self):
    project = self.param_dict['project']
  
    #Set up database connection
    conn = self.get_db_connection()
    cur = conn.cursor()
      
    #Create neccesary tables for the project
    try:
      cur.execute(open("database/MTurk_create.sql", "r").read().format(project))
      conn.commit()
      cur.close()
      conn.close()
      self.logger.log('success', 'Tables for MTurk Connecter are configured.')
    except:
      self.logger.log('danger', 'Fail to configured tables for MTurk connector.')
      conn.rollback()
      cur.close()
      conn.close()
      traceback.print_exc()
      sys.exit()
  
  #Clear trash record in pending and answer table)
  def clear_trash_record(self):
    project = self.param_dict['project']
    conn = self.get_db_connection()
    try:
      rowAffect = 0
      cur = conn.cursor()
      cur.execute('''TRUNCATE TABLE "{0}"'''.format(project + '_pending'))
      rowAffect = rowAffect + cur.rowcount
      cur.execute('''TRUNCATE TABLE "{0}"'''.format(project + '_answers'))
      rowAffect = rowAffect + cur.rowcount
      conn.commit()
      conn.close()
      if rowAffect > 0:
        self.logger.log('warning', 'Trash MTurk pending records are detected and removed.')
    except Exception, e:
      self.logger.log('warning', 'Fail to clear trash records. ' + e.message)
      traceback.print_exc()
      conn.rollback()
      conn.close()

  def clear_tables(self):
    project = self.param_dict['project']
    
    conn = self.get_db_connection()
    cur = conn.cursor()
    
    try:
      cur.execute(open("database/MTurk_remove.sql", "r").read().format(project))
      conn.commit()
      cur.close()
      conn.close()
    except:
      self.logger.log('danger', 'Fail to reset tables.')
      traceback.print_exc()
      conn.rollback()
      conn.close()
      
      
  def get_auto_header(self):
    question_path = self.param_dict['q_path']
                    
    if not os.path.exists(question_path):
      self.logger.log('danger', 'Question file not found.')
      sys.exit()
    else:
      header = []
      question = None
      with open(question_path, 'r') as q_file:
        question = q_file.readlines()
        for line in question:
          if '${' in line and '}' in line:
            tmps = line.split('${')[1:]
            for tmp in tmps:
              header.append(tmp.split('}')[0])
      return header
      
  def check_files(self):
    p_path = self.param_dict['p_path']
    q_path = self.param_dict['q_path']
    
    if p_path == '':
      self.logger.log('danger', 'Path to question file is not configured.')
      return False
    if q_path == '':
      self.logger.log('danger', 'Path to properties file is not configured.')
      return False
    if not os.path.exists(q_path):
      self.logger.log('danger', 'Question file not found.')
      return False
    if not os.path.exists(p_path):
      self.logger.log('danger', 'Properties file not found.')
      return False
      
    return True
      
  
  '''-------------------Backup of no long used functions-----------------'''
  '''
  #transform properties dict to properties file format
  def dict2properties(self, d):
    output = ''
    if isinstance(d, dict):
      for key, value in dict.items(d):
        output = output + key + ':' + str(value) + '\n'
    return output
  
  #Delete hits in a .success file. Slow but safe commond line version (auto approve and expire)
  def delete_hits(self):
    if not os.path.isfile(self.get_label() + '.success'):
      print "File " + self.get_label() + '.success not found'
      return
    cmd = self.set_cmd("deleteHITs")
    cmd = cmd + ' -successfile ' + self.get_label() + '.success'
    cmd = cmd + ' -approve'
    cmd = cmd + ' -expire'
    cmd = cmd + ' -force'
    action = my_utils.run_cmd(cmd)
    try:
      os.remove(self.get_label() + '.success')
      os.remove(self.get_label() + '.failure')
    except OSError:
      pass
    return action
    
  #Delete hits in a .success file. fast API version (auto approve and expire)
  def delete_hits_api(self):
    if not os.path.isfile(self.get_label() + '.success'):
      print "File " + self.get_label() + '.success not found'
      return
    if self.boto_mtc is None:
      print "MTurk API is not connected because of missing keys."
      return
    with open(self.get_label() + '.success', 'rb') as success_file:
      reader = csv.reader(success_file, delimiter='\t')
      next(reader, None)
      for row in reader:
        try:
          hit_id=row[0]
          self.boto_mtc.disable_hit(hit_id)
          print "[" + hit_id + "] has been deleted successfully."
        except:
          print "[" + hit_id + "] Failed to delete hit."
    try:
      os.remove(self.get_label() + '.success')
    except OSError:
      pass
  
  #Get result: API version (bojo), prototype
  def get_results_api(self, label):
    if not os.path.isfile(label + '.success'):
      print "File " + label + '.success not found'
      return
    if self.boto_mtc is None:
      print "MTurk API is not connected because of missing keys."
      return
    with open(label + '.success', 'rb') as success_file:
      reader = csv.reader(success_file, delimiter='\t')
      next(reader, None)
      assignments = []
      for row in reader:
        hit_id=row[0]
        try:
          assignments = self.boto_mtc.get_assignments(hit_id)
          row = "Result of " + hit_id + ": "
          for assignment in assignments:
            for answer in assignment.answers[0]:
              for value in answer.fields:
                row = row + '\t' + value
          print row
        except:
          print "Fail to get result for hit " + hit_id
  
  #approve or reject sumbitted results according to results file
  def review_results(self, label):
    if not os.path.isfile(label + '.results'):
      print "File " + label + '.results not found'
      return
    cmd = self.set_cmd("reviewResults")
    cmd = cmd + ' -resultsfile ' + label + '.results'
    return my_utils.run_cmd(cmd)
  '''
