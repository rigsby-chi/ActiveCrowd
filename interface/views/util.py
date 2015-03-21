from flask import render_template, redirect, flash
import os, json, psycopg2, traceback
import ast

def getRelativePath(path):
  return os.path.join(os.path.dirname(__file__), path)

def needSetup():
  """Check whether the framework is setup
  
  Returns:
      A boolean of whether the framework is setup
  """
   if os.path.exists(getRelativePath('config.json')):
      return False
   else:
      return True
      
def _render_template(template_path, parameter=None):
  """Render a requested template
  
  Force use to stay on either welcome, setup or about page if the frameword is 
  not setup yet
  
  Args:
      template_path: A string of the path to the HTML template 
      parameter: A dict of the parameter for template rendering
  
  Returns:
      A rendered template or a redirection to home page
  """
  if needSetup() and not (template_path == 'general/welcome.html' or 
                      template_path == 'general/setup.html' or 
                      template_path == 'general/about.html'):
    return redirect('/')
  else:
    return render_template(template_path, needSetup = needSetup(), parameter=parameter)
    
    
#Get a database connection object
def getDBConnection(dbname, user, password):
  """Get a database connection object from parameters
  
  Args:
      dbname: A string of the database name
      user: A string of the database user name
      password: A string of the database user password
  
  Returns:
      A database connection object
  """
  try:
    conn_details = "dbname='{0}' ".format(dbname) + \
                   "user='{0}' ".format(user) + \
                   "password='{0}'".format(password)
    conn = psycopg2.connect(conn_details)
    return (True, conn)
  except:
    traceback.print_exc()
    return (False, 'Unable to connect to the database with the provided details.')

#Get a database connection object from configuration file
def getDBConnectionFromConfig():
  """Get a database connection object from configuation file
  
  Returns:
      A database connection object
  """
  if os.path.exists(getRelativePath('config.json')):
    with open(getRelativePath('config.json')) as configFile:
      config = json.load(configFile)
      return getDBConnection(config['DBName'], config['DBUser'], config['DBPassword'])
  else:
    return (False, 'Config file not found')

def getDBFromConfig():
  """Get database access details from configuation file
  
  Returns:
      A dict of databse access details
  """
  if os.path.exists(getRelativePath('config.json')):
    with open(getRelativePath('config.json')) as configFile:
      config = json.load(configFile)
      db = {}
      db['db'] = config['DBName']
      db['db_user'] = config['DBUser']
      db['db_password'] = config['DBPassword']
      return db

    
#Get default mturk access from configuration file
def getDefaultMTurkAccess():
  if os.path.exists(getRelativePath('config.json')):
    with open(getRelativePath('config.json')) as configFile:
      config = json.load(configFile)
      return {'AWSKey':config['AWSKey'], 'AWSSecretKey': config['AWSSecretKey']}
  else:
    return (False, 'Config file not found')
    
def getProjectName():
  """Get the name of all existing project
  
  Returns:
      A list of project names
  """
  conn = getDBConnectionFromConfig()
  if conn[0]:
    conn = conn[1]
    cur = conn.cursor()
    cur.execute('SELECT name FROM project ORDER BY name')
    rows = cur.fetchall()
    projectName = []
    for row in rows:
      projectName.append(row[0])
    conn.close()
    return projectName
  else:
    return ['<Error!>']
    
def getProjectDetails(projectName):
  """Get all details of a project:
  
  Args:
      projectName: A string of the name of the project
      
  Returns:
      A dict contain all details of a project
  """
  conn = getDBConnectionFromConfig()[1]
  cur = conn.cursor()
  cur.execute('''SELECT * FROM project WHERE name=%s''', (projectName,))
  rows = cur.fetchall()
  detailDict = {
    'projectName'         : projectName,
    'projectDescription'  : rows[0][1],
    'useMTurk'            : rows[0][2],
    'MTurkDetail'         : rows[0][3],
    'sklearnMode'         : rows[0][4],
    'sklearnDetail'       : rows[0][5],
    'functions'           : rows[0][6]
  }
  
  if detailDict['sklearnMode'] == 'SVC' or detailDict['sklearnMode'] == 'NuSVC':
    detailDict['learningAlgorithm'] = 'SVM'
  elif detailDict['sklearnMode'] == 'DecisionTreeClassifier':
    detailDict['learningAlgorithm'] = 'DT'
  elif detailDict['sklearnMode'] == 'GaussianNB' or detailDict['sklearnMode'] == 'MultinomialNB' or detailDict['sklearnMode'] == 'BernoulliNB':
    detailDict['learningAlgorithm'] = 'NB'
  elif detailDict['sklearnMode'] == 'KNeighborsClassifier':
    detailDict['learningAlgorithm'] = 'NN'
  
  if detailDict['MTurkDetail'] is not None:
    MTurkDetail = ast.literal_eval(detailDict['MTurkDetail'])
    detailDict = dict(detailDict.items() + MTurkDetail.items())
  
  if detailDict['sklearnDetail'] is not None:
    sklearnFields = ast.literal_eval(detailDict['sklearnDetail'])
    detailDict = dict(detailDict.items() + sklearnFields.items())
    
  if detailDict['functions'] is not None:
    functions = ast.literal_eval(detailDict['functions'])
    detailDict = dict(detailDict.items() + functions.items())
    
  conn.close()
  return detailDict
    
def s2cMessage(messageType, message):
  """Add a server side message to session for client side display
  
  Args:
      messageType: A string of the message type, could be either info, success, danger, warning
      message: A string of the message content
  """
  flash(messageType + ':::' + message + ';;;')
  
def isProjectExists(projectName):
  """Check if a project name is already in use
  
  Args:
      projectName: A string of the project name
      
  Returns:
      A boolean of whether the project name is already in use
  """
  try:
    conn = getDBConnectionFromConfig()[1]
    cur = conn.cursor()
    cur.execute('SELECT name FROM project WHERE name=%s', (projectName, ))
    rows = cur.fetchall()
    if len(rows) > 0:
      return True
    else:
      return False
  except:
    return False
    
def checkProjectStatus(projectName):
  resultDict = {
    'MTurk'      : 'remove',
    'PFile'      : 'remove',
    'QFile'      : 'remove',
    'SKLearn'    : 'remove',
    'Function'   : 'remove',
    'PYFile'     : 'remove',
    'MTurkMsg'   : 'Not configured',
    'PFileMsg'   : 'Not available',
    'QFileMsg'   : 'Not available',
    'SKLearnMsg' : 'Not available',
    'FunctionMsg': 'Not available',
    'PYFileMsg'  : 'Pre-requirement not fulfilled'
  }
  
  conn = getDBConnectionFromConfig()[1]
  cur = conn.cursor()
  cur.execute('SELECT useMTurk, sklearnDetail, functions, has_changes FROM project WHERE name=%s', (projectName, ))
  rows = cur.fetchall()
  if rows[0][0] is 1:
    resultDict['MTurk'] = 'ok'
    resultDict['MTurkMsg'] = 'Enabled'
    if os.path.exists('project/' + projectName + '/_mturk.properties'): 
      resultDict['PFile'] = 'ok'
      resultDict['PFileMsg'] = 'File is found'
    if os.path.exists('project/' + projectName + '/_mturk.question'): 
      resultDict['QFile'] = 'ok'
      resultDict['QFileMsg'] = 'File is found'
      
  elif rows[0][0] is 2:
    resultDict['MTurk'] = 'warning'
    resultDict['MTurkMsg'] = 'Disabled'
    resultDict['PFile'] = 'info'
    resultDict['PFileMsg'] = 'Not applicable'
    resultDict['QFile'] = 'info'
    resultDict['QFileMsg'] = 'Not applicable'
    resultDict['Function'] = 'info'
    resultDict['FunctionMsg'] = 'Not applicable'
    
  if rows[0][1] is not None and rows[0][0] is not '':
    resultDict['SKLearn'] = 'ok'
    resultDict['SKLearnMsg'] = 'Configuration is Found'
  if rows[0][2] is not None and rows[0][0] is not '':
    resultDict['Function'] = 'ok'
    resultDict['FunctionMsg'] = 'Functions are defined'
    
  if os.path.exists('project/' + projectName + '/execute.py'): 
    resultDict['PYFile'] = 'ok'
    resultDict['PYFileMsg'] = 'File is found'
  elif (resultDict['MTurk'] == 'ok' and \
       resultDict['QFile'] == 'ok' and \
       resultDict['PFile'] == 'ok' and \
       resultDict['SKLearn'] == 'ok' and \
       resultDict['Function'] == 'ok') or \
       (resultDict['MTurk'] == 'warning' and \
       resultDict['SKLearn'] == 'ok'):
    resultDict['PYFile'] = 'info'
    resultDict['PYFileMsg'] = 'Ready to generate execution file'
  
  resultDict['hasChanges'] = int(rows[0][3])
  return resultDict
    

#Parse Properties file into attributes
def getPFileInfo(projectName):
  """Get properties file configuration from a properties file
  
  Args:
      projectName: A string of the project name
      
  Returns:
      A dict object of the properties file configuration
  """
  PDict = {}
  
  def searchLineWithPrefix(lines, prefix):
    """Search the line that containing a specific prefix
    
    Args:
        lines: An iterable type storing strings
        prefix: A string of prefix to be searched
        
    Returns:
        A string that matching the prefix
    """
    for line in lines:
      if(line.startswith(prefix)):
        return line
        
  try:
    if os.path.exists('project/' + projectName + '/_mturk.properties'):
      with open('project/' + projectName + '/_mturk.properties') as PFile:
        lines = PFile.readlines()
        PDict['HITTitle'] = searchLineWithPrefix(lines, 'title:').split(":",1)[1]
        PDict['HITDescription'] = searchLineWithPrefix(lines, 'description:').split(":",1)[1]
        PDict['HITKeywords'] = searchLineWithPrefix(lines, 'keywords:').split(":",1)[1]
        PDict['HITReward'] = float(searchLineWithPrefix(lines, 'reward:').split(":",1)[1])
        PDict['HITAssignments'] = searchLineWithPrefix(lines, 'assignments:').split(":",1)[1]
        PDict['HITAnnotation'] = searchLineWithPrefix(lines, 'annotation:').split(":",1)[1]
        PDict['HITDuration'] = int(searchLineWithPrefix(lines, 'assignmentduration:').split(":",1)[1])
        PDict['HITLifetime'] = int(searchLineWithPrefix(lines, 'hitlifetime:').split(":",1)[1])
        PDict['HITApprovalDelay'] = int(searchLineWithPrefix(lines, 'autoapprovaldelay:').split(":",1)[1])
    return PDict
  except:
    PDict['Error'] = 'The system detected a high oppotunity that the properties file is parsed wrongly.'; 
    return PDict

#Parse Question file into attributes
def getQFileInfo(projectName):
  """Get question file configuration from a question file
  
  Args:
      projectName: A string of the project name
      
  Returns:
      A dict object of the quesiton file configuration
  """
  QDict = {}
  try:
    if os.path.exists('project/' + projectName + '/_mturk.question'):
      with open('project/' + projectName + '/_mturk.question') as QFile:
        lines = QFile.read()
        QDict['NumberOfQuestion'] = lines.count("<Question>")
        
        QDict['QuestionTitle'] = lines.split("<Title>")[1]
        QDict['QuestionTitle'] = QDict['QuestionTitle'].split("</Title>")[0]
        
        QDict['QuestionOverview'] = lines.split("</Title>")[1]
        QDict['QuestionOverview'] = QDict['QuestionOverview'].split("<FormattedContent><![CDATA[")[1]
        QDict['QuestionOverview'] = QDict['QuestionOverview'].split("]]></FormattedContent>")[0]
        
        QDict['DisplayName'] = lines.split("<DisplayName>")[1]
        QDict['DisplayName'] = QDict['DisplayName'].split("</DisplayName>")[0]
        
        QDict['QuestionContent'] = lines.split("<QuestionContent>")[1]
        QDict['QuestionContent'] = QDict['QuestionContent'].split("<FormattedContent><![CDATA[")[1]
        QDict['QuestionContent'] = QDict['QuestionContent'].split("]]></FormattedContent>")[0]
        
        #If more than one question in a hit, remove the appended number of placeholders
        if QDict['NumberOfQuestion'] > 1:
          temp = QDict['QuestionContent'].split('${')
          QDict['QuestionContent'] = temp[0]
          for t in temp[1:]:
            temp2 = t.split('}')
            QDict['QuestionContent'] = QDict['QuestionContent'] + '${' + temp2[0][:-1]
            for t2 in temp2[1:]:
              QDict['QuestionContent'] = QDict['QuestionContent'] + '}' + t2
            
        TempAnswerType = lines.split("<AnswerSpecification>")[1].split("<")[1].split(">")[0]
        
        #Get configuration of different answer type
        if TempAnswerType == "SelectionAnswer":
          QDict['AnswerType'] = 'Selection'
          Selections = lines.split("<Selections>")[1]
          Selections = Selections.split("</Selections>")[0]
          Selections = Selections.split("<Selection>")[1:]
          Selections = [selection.split("</Selection>")[0] for selection in Selections]
          value = [selection.split("<SelectionIdentifier>")[1] for selection in Selections]
          value = [v.split("</SelectionIdentifier>")[0] for v in value]
          text = [selection.split("<Text>")[1] for selection in Selections]
          text = [t.split("</Text>")[0] for t in text]
          QDict['Selections'] = zip(text, value)
          
        elif TempAnswerType == "FreeTextAnswer" and "AnswerFormatRegex" in lines:
          QDict['AnswerType'] = 'FreeTextRegex'
          QDict['FreeTextRegex'] = lines.split("<AnswerFormatRegex regex=\"")[1].split("\" errorText=\"")[0]
          QDict['ErrorMessage'] = lines.split("\" errorText=\"")[1].split("\"/>")[0]
          
        elif TempAnswerType == "FreeTextAnswer" and "<IsNumeric" in lines:
          QDict['AnswerType'] = 'Numeric'
          if '<IsNumeric ' in lines and 'minValue="' in lines:
            QDict['minValue'] = int(lines.split('<IsNumeric ')[1].split('minValue="')[1].split('"')[0])
          if '<IsNumeric ' in lines and 'maxValue="' in lines:
            QDict['maxValue'] = int(lines.split('<IsNumeric ')[1].split('maxValue="')[1].split('"')[0])
            
        elif TempAnswerType == "FreeTextAnswer":
          QDict['AnswerType'] = 'FreeText' 
          
        elif TempAnswerType == "FreeTextAnswer":
          QDict['AnswerType'] = 'FreeText' 
      
    return QDict
  except:
    QDict['Error'] = 'The system detected a high oppotunity that the question file is parsed wrongly.'; 
    return QDict
    
def formatContent(content):
  result = ''
  if '{' in content or '}' in content:
    for i in range(0, len(content)):
      result += content[i]
      if content[i] == '{' or content[i] == '}':
        result += content[i]
  else:
    result = content
  return result

class Logger(object):
  """Enable logging of exeuctions
  
  Attributes:
      db_conn: A database connection object
      project: A string of the project name
  """
  db_conn = None
  project = None
  
  def __init__(self, project):
    """Initialization of logger object
    
    Args:
        project: A string of the project name
    """
    self.project = project
    self.db_conn = getDBConnectionFromConfig()[1]
    
  def log(self, msg_type, message):
    """Log a message
    
    Args:
        msg_type: A string of the type of message. Could be either of info, success, danger and warning
        message: A string of the content of the message
    """
    if not self.db_conn is None:
      cur = self.db_conn.cursor()
      print '[' + msg_type + '] ' + message
      cur.execute('INSERT INTO "{0}_logs" (time, type, message) ' + \
                  'VALUES (CURRENT_TIMESTAMP, %s, %s)'.format(self.project), (msg_type, message,))
      self.db_conn.commit()
      
class Recorder(object):
  """Enable recording of important events or the project stage at a moment
  
  Attributes:
      db_conn: A database connection object
      project: A string of the project name
  """
  db_conn = None
  project = None
  
  def __init__(self, project):
    """Initialization of recorder object
    
    Args:
        project: A string of the project name
        db: A string of the name of the target database
        db_user: A string of the database user name
        db_password: A stirng of the database user passowrd
    """
    self.project = project
    self.db_conn = getDBConnectionFromConfig()[1]
    
  def record(self, recordType):
    """Record an event or a stage
    
    Args:
        recordType: A string of the type of record picked up by handler
    """
    if not self.db_conn is None:
      cur = self.db_conn.cursor()
      cur.execute('INSERT INTO "{0}_learning_records" (time, record_type) ' + \
                  """VALUES (CURRENT_TIMESTAMP, '{1}')""".format(self.project, recordType))
      self.db_conn.commit()
