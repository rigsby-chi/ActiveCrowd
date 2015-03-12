import os, traceback
from flask import request, Blueprint, redirect
from util import _render_template, getDBConnectionFromConfig, s2cMessage, getPFileInfo, getQFileInfo, formatContent
from projectExecution import isProcessAlive

PROPERTIES_TEMPLATE = 'templates/properties.template'
QUESTION_TEMPLATE = 'templates/question.template'
QUESTION_TEMPLATE_FT = 'templates/question_ft.template'
QUESTION_TEMPLATE_FTR = 'templates/question_ftr.template'
QUESTION_TEMPLATE_N = 'templates/question_n.template'
QUESTION_TEMPLATE_S = 'templates/question_s.template'
SELECTION_TEMPLATE = 'templates/selection.template'
EXE_DEF_TEMPLATE = 'templates/exe_def.template'

mod = Blueprint('projectSetting', __name__, url_prefix='/project/<projectName>/setting')

@mod.route('/mturk', methods=['GET','POST'])
def mturk(projectName):
  parameter = {
    'projectName'         : projectName,
    'inExecution'         : isProcessAlive(projectName)
  }
  if request.method == 'GET':
    from util import getProjectDetails, getDefaultMTurkAccess
    parameter = dict(parameter.items() + getProjectDetails(projectName).items())

    if 'AWSKey' not in parameter or 'AWSSecretKey' not in parameter:
      parameter = dict(parameter.items() + getDefaultMTurkAccess().items())

    if parameter['useMTurk']==0 or parameter['useMTurk']==1:
      parameter['isChecked'] = 'checked'

    if parameter['useMTurk']==1 or parameter['useMTurk']==2:
      PDict = getPFileInfo(projectName)
      if 'Error' in PDict:
        s2cMessage('warning', PDict['Error'])
      parameter = dict(parameter.items() + PDict.items())
        
      QDict = getQFileInfo(projectName)
      if 'Error' in QDict:
        s2cMessage('warning', QDict['Error'])
      parameter = dict(parameter.items() + QDict.items())
      
    return _render_template('project/setting/mturk.html', parameter)
  elif request.method == 'POST':
    try:
      #Get database connection
      conn = getDBConnectionFromConfig()[1]
      cur = conn.cursor()
    
      if 'useMTurk' in request.form:
      
        #Properties File
        if request.form['UorBPFile'] == 'option1':
          PFile = request.files['PFile']
          PFile.save(os.path.join('project/' + projectName, '_mturk.properties'))
          
        #Render properties file from templates
        elif request.form['UorBPFile'] == 'option2':
          HITTitle=           str(request.form['HITTitle'])
          HITDescription=     str(request.form['HITDescription'])
          HITKeywords=        str(request.form['HITKeywords'])
          HITAnnotation=      str(request.form['HITAnnotation'])
          HITReward=          float(request.form['HITReward'])
          HITAssignments=     int(request.form['HITAssignments'])
          HITDuration=        int(request.form['HITDuration'])
          HITLifetime=        int(request.form['HITLifetime'])
          HITApprovalDelay=   int(request.form['HITApprovalDelay'])
          with open(PROPERTIES_TEMPLATE) as PTemplate:
            with open('project/' + projectName + '/_mturk.properties', "w") as PFile:
              PFile.write(PTemplate.read().format(HITTitle, HITDescription, HITKeywords, \
                            HITReward, HITAssignments, HITAnnotation, HITDuration, \
                            HITLifetime, HITApprovalDelay))
                            
        #Question file
        if request.form['UorBQFile'] == 'option1':
          QFile = request.files['QFile']
          QFile.save(os.path.join('project/' + projectName, '_mturk.question'))
          
        #Render question file from templates
        elif request.form['UorBQFile'] == 'option2':
          NumberOfQuestion=  int(request.form['NumberOfQuestion'])
          QuestionTitle=     str(request.form['QuestionTitle'])
          QuestionOverview=  str(request.form['QuestionOverview'])
          DisplayName=       str(request.form['DisplayName'])
          QuestionContent=   str(request.form['QuestionContent'])
          AnswerType=        str(request.form['AnswerType'])
          FreeTextRegex=     str(request.form['FreeTextRegex'])
          ErrorMessage=      str(request.form['ErrorMessage'])
          minValue=          parseOptionalInt(request.form['minValue'])
          maxValue=          parseOptionalInt(request.form['maxValue'])
          
          QuestionContent = formatContent(QuestionContent)
          #If more than one question in a HIT, create unique placeholder name
          if NumberOfQuestion > 1 and '${' in QuestionContent and '}' in QuestionContent:
            temp = QuestionContent.split('${{')
            QuestionContent = temp[0]
            for t in temp[1:]:
              temp2 = t.split('}}')
              QuestionContent = QuestionContent + '${{' + temp2[0] + '{0}'
              for t2 in temp2[1:]:
                QuestionContent = QuestionContent + '}}' + t2
          
          #Fit different question answer type
          if AnswerType == 'FreeText':
            question = open(QUESTION_TEMPLATE_FT).read().format('{0}', formatContent(DisplayName), QuestionContent)
          elif AnswerType == 'FreeTextRegex':
            question = open(QUESTION_TEMPLATE_FTR).read().format('{0}', formatContent(DisplayName), \
                            QuestionContent, formatContent(FreeTextRegex), \
                            formatContent(ErrorMessage))
           #<img src="${image}" alt="image" width="180" height="180"></img>
          elif AnswerType == 'Numeric':
            print 1
            constraint = ''
            if not minValue is None:
              constraint = constraint + ' minValue="' + str(minValue) + '"'
            if not maxValue is None:
              constraint = constraint + ' maxValue="' + str(maxValue) + '"'
            question = open(QUESTION_TEMPLATE_N).read().format('{0}', formatContent(DisplayName), QuestionContent, constraint)
          elif AnswerType == 'Selection':
            question = open(SELECTION_TEMPLATE).read()
            i = 0
            selections = ''
            while 'sel_' + str(i) in request.form and 'seln_' + str(i) in request.form:
              sValue = request.form['sel_' + str(i)]
              sText = request.form['seln_' + str(i)]
              selections = selections + open(SELECTION_TEMPLATE).read().format(sValue, sText)
              i = i + 1
              
            question = open(QUESTION_TEMPLATE_S).read().format('{0}', formatContent(DisplayName), \
                            QuestionContent, selections)
          
          #Generate question file
          questions = ''
          for j in range(0, NumberOfQuestion):
            questions = questions + question.format(j)
          
          with open(QUESTION_TEMPLATE) as QTemplate:
            with open('project/' + projectName + '/_mturk.question', "w") as QFile:
              QFile.write(QTemplate.read().format(QuestionTitle, QuestionOverview, questions))
        
        #Update Database Record
        MTurkDetail = {
          'AWSKey'                : str(request.form['AWSKey']),
          'AWSSecretKey'          : str(request.form['AWSSecretKey']),
          'samplesPerHIT'         : int(request.form['samplesPerHIT']),
          'HITsPerIteration'      : int(request.form['HITsPerIteration']),
          'threshold'             : int(request.form['threshold']),
          'intervalInSecond'      : int(request.form['intervalInSecond']),
          'enlargeSamplingRange'  : int(request.form['enlargeSamplingRange']),
          'controlGroupRadio'     : int(request.form['controlGroupRadio'])
        }
        
        QuestionsInQFile = getQFileInfo(projectName)['NumberOfQuestion']
        if not QuestionsInQFile == MTurkDetail['samplesPerHIT']:
          MTurkDetail['samplesPerHIT'] = QuestionsInQFile
          s2cMessage('warning', 'User defined "Samples Per HIT" value is inconsistent to the number of questions in the uploaded question file. The later one is used instead.')
          
        cur.execute('UPDATE project SET (useMTurk, MTurkDetail) = (1, %s) WHERE name = %s', \
                (str(MTurkDetail), projectName, ))
        conn.commit()
        conn.close()
        
      else:
        #Update Database Record
        cur.execute('UPDATE project SET useMTurk = 2 WHERE name = %s', (projectName, ))
        conn.commit()
        conn.close()
      setHasChanges(projectName)
      s2cMessage('success', 'MTurk configuration completed.')
      return redirect('project/' + projectName + '/overview')
    except Exception, e:
      traceback.print_exc()
      s2cMessage('danger', 'Unexpected error: ' + e.message)
      return redirect('project/' + projectName + '/overview')
  
@mod.route('/sklearn', methods=['GET','POST'])
def sklearn(projectName):
  parameter = {
    'projectName'         : projectName,
    'inExecution'         : isProcessAlive(projectName)
  }
  if request.method == 'GET':
    from util import getProjectDetails
    parameter = dict(parameter.items() + getProjectDetails(projectName).items())
    return _render_template('project/setting/sklearn.html', parameter)
  
  elif request.method == 'POST':
    try:
      setting = ''
      
      classifierClass = str(request.form['classifierClass'])
      setting  = {}
      if classifierClass == 'SVC' or classifierClass == 'NuSVC':
        setting = {
          'kernel'            :str(request.form['kernel']),
          'degree'            :int(request.form['degree']),
          'gamma'             :float(request.form['gamma']),
          'coef0'             :float(request.form['coef0']),
          'shrinking'         :parseHTMLBool(request.form['shrinking']),
          'probability'       :True,
          'tol'               :float(request.form['tol']),
          'cache_size'        :float(request.form['cache_size']),
          'class_weight'      :None,
          'verbose'           :parseHTMLBool(request.form['verbose']),
          'max_iter'          :int(request.form['max_iter']),
          'random_state'      :parseOptionalInt(request.form['random_state'])
        }
        if classifierClass == 'SVC':
          setting['C'] = float(request.form['C'])
        elif classifierClass == 'NuSVC':
          setting['nu'] = float(request.form['nu'])
          
      elif classifierClass == 'DecisionTreeClassifier':
        setting = {
          'criterion'              :str(request.form['criterion']),
          'splitter'               :str(request.form['splitter']),
          'max_features'           :str(request.form['max_features']),
          'max_depth'              :parseOptionalInt(request.form['max_depth']),
          'min_samples_split'      :parseOptionalInt(request.form['min_samples_split']),
          'min_samples_leaf'       :parseOptionalInt(request.form['min_samples_leaf']),
          'max_leaf_nodes'         :parseOptionalInt(request.form['max_leaf_nodes']),
          'random_state'           :parseOptionalInt(request.form['random_state'])
        }
        if setting['max_features'] == 'None':
          setting['max_features'] = None
      
      elif classifierClass == 'GaussianNB':
        setting = {}
      elif classifierClass == 'MultinomialNB' or classifierClass == 'BernoulliNB':
        setting = {
          'alpha'              :float(request.form['alpha']),
          'fit_prior'          :False,  #parseHTMLBool(request.form['fit_prior']),
          'class_prior'        :None
        }
        if classifierClass == 'BernoulliNB':
          setting['binarize'] = parseOptionalFloat(request.form['binarize'])
          
      elif classifierClass == 'KNeighborsClassifier':
        setting = {
          'n_neighbors'            :int(request.form['n_neighbors']),
          'weights'                :str(request.form['weights']),
          'leaf_size'              :int(request.form['leaf_size']),
          'algorithm'              :str(request.form['algorithm']),
          'metric'                 :str(request.form['metric']),
          'p'                      :int(request.form['p']),
          'metric_params'          :str(request.form['metric_params'])
        }
        if setting['metric_params'] == 'None':
          setting['metric_params'] = None
        elif setting['metric_params'][0] == '{' and setting['metric_params'][-1] == '}':
          #Dict input
          try:
            import ast
            setting['metric_params'] = ast.literal_eval(setting['metric_params'])
          except Exception, e:
            setting['metric_params'] = None
            s2cMessage('danger', 'Undefined metric_params. None value is set instead. (' + e.message + ')')
        else:
          setting['metric_params'] =  None

      conn = getDBConnectionFromConfig()[1]
      cur = conn.cursor()
      cur.execute('UPDATE project SET (sklearnMode, sklearnDetail) = (%s, %s) WHERE name = %s', \
                (classifierClass, str(setting), projectName, ))
      conn.commit()
      conn.close()
      setHasChanges(projectName)
      s2cMessage('success', 'SKLearn configuration completed.')
      return redirect('project/' + projectName + '/overview')
    except Exception, e:
      traceback.print_exc()
      s2cMessage('danger', 'Unexpected error: ' + e.message)
      return redirect('project/' + projectName + '/overview')
      
@mod.route('/function', methods=['GET','POST'])
def function(projectName): 
  parameter = {
    'projectName'         : projectName,
    'inExecution'         : isProcessAlive(projectName)
  }
  if request.method == 'GET':
    from util import getProjectDetails
    parameter = dict(parameter.items() + getProjectDetails(projectName).items())
    return _render_template('project/setting/function.html', parameter)
  elif request.method == 'POST':
    try:
      functions = {
        'sample2Info': request.form['sample2Info'],
        'answer2Label': request.form['answer2Label']
      }
      
      conn = getDBConnectionFromConfig()[1]
      cur = conn.cursor()
      cur.execute('UPDATE project SET functions = %s WHERE name = %s', \
                (str(functions), projectName, ))
      conn.commit()
      conn.close()
      setHasChanges(projectName)
      s2cMessage('success', 'Function configuration completed.')
      return redirect('project/' + projectName + '/overview')
    except Exception, e:
      traceback.print_exc()
      s2cMessage('danger', 'Unexpected error: ' + e.message)
      return redirect('project/' + projectName + '/overview')
      
def parseHTMLBool(htmlBool):
  if htmlBool == 'True':
    return True
  else:
    return False
    
def parseOptionalInt(htmlInt):
  try:
    return int(htmlInt)
  except ValueError:
    return None
    
def parseOptionalFloat(htmlFloat):
  try:
    return float(htmlFloat)
  except ValueError:
    return None
    
def setHasChanges(projectName):
  conn = getDBConnectionFromConfig()[1]
  cur = conn.cursor()
  cur.execute('UPDATE project SET has_changes = 1 WHERE name = %s', (projectName, ))
  conn.commit()
  conn.close()
