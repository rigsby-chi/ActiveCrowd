import os, traceback, imp, shutil
from flask import flash, request, Blueprint, jsonify, redirect, url_for
from multiprocessing import Process
from util import _render_template, getDBConnectionFromConfig, s2cMessage, Logger, Recorder, getProjectDetails, getDBFromConfig, checkProjectStatus

EXE_SVC_TEMPLATE = 'templates/exe_SVC.template'
EXE_SVC_NU_TEMPLATE = 'templates/exe_SVC_N.template'
EXE_SVC_L_TEMPLATE = None
EXE_DT_TEMPLATE = 'templates/exe_DT.template'
EXE_NB_G_TEMPLATE = 'templates/exe_NB_G.template'
EXE_NB_M_TEMPLATE = 'templates/exe_NB_M.template'
EXE_NB_B_TEMPLATE = 'templates/exe_NB_B.template'
EXE_NN_K_TEMPLATE = 'templates/exe_NN_K.template'
EXE_DEF_TEMPLATE = 'templates/exe_def.template'
EXE_DEF_NULL_TEMPLATE = 'templates/exe_def_null.template'
MC_TEMPLATE = 'templates/mturk_connector.template'
MC_NULL_TEMPLATE = 'templates/mturk_connector_null.template'
AUTO_TEMPLATE = 'templates/auto.template'
AUTO_NULL_TEMPLATE = 'templates/auto_null.template'
CLEAR_MTURK_TEMPLATE = 'templates/clear_MTurk.template'

mod = Blueprint('projectExecution', __name__, url_prefix='/project/<projectName>/execution')

caProcess = {}

def isProcessAlive(projectName):
  if projectName in caProcess and caProcess[projectName][0].is_alive():
    return caProcess[projectName][1]
  else:
    return False

@mod.route('/', methods=['GET','POST'])
def execution(projectName): 
  parameter = {
    'projectName'         : projectName,
    'inExecution'         : isProcessAlive(projectName)
  }
  global caProcess
  if request.method == 'GET':
    parameter = dict(parameter.items() + checkProjectStatus(projectName).items())
    if parameter['PYFile'] == 'ok':
      if parameter['hasChanges'] == 1:
        s2cMessage('warning', 'New settings are detected. Please re-generate exeuction files to activate them.')
      if parameter['inExecution'] == 'training':
        parameter['useSandbox'] = caProcess[projectName][2]
        parameter['stopAtErrorRate'] = caProcess[projectName][3]
        parameter['stopAtSampleAmount'] = caProcess[projectName][4]
      return _render_template('project/execution/execution.html', parameter)
    if parameter['PYFile'] == 'remove':
      parameter['isReady'] = False
      s2cMessage('warning', 'Pre-requirement not fulfilled. Please check the following status.')
    return _render_template('project/execution/generation.html', parameter)
    
  elif request.method == 'POST':
    #Generation of execution procedures
    if 'generate' in request.form:
      try:
        projectStatus = checkProjectStatus(projectName)
        if not projectStatus['PYFile'] == 'info':
          return redirect('project/' + projectName + '/execution')
          
        db = getDBFromConfig()
        details = getProjectDetails(projectName)
        
        template = None
        if details['sklearnMode'] == 'SVC':
          template = EXE_SVC_TEMPLATE
        elif details['sklearnMode'] == 'NuSVC':
          template = EXE_SVC_NU_TEMPLATE
        elif details['sklearnMode'] == 'DecisionTreeClassifier':
          template = EXE_DT_TEMPLATE
        elif details['sklearnMode'] == 'GaussianNB':
          template = EXE_NB_G_TEMPLATE
        elif details['sklearnMode'] == 'MultinomialNB':
          template = EXE_NB_M_TEMPLATE
        elif details['sklearnMode'] == 'BernoulliNB':
          template = EXE_NB_B_TEMPLATE
        elif details['sklearnMode'] == 'KNeighborsClassifier':
          template = EXE_NN_K_TEMPLATE
        
        if projectStatus['MTurk'] == 'ok':
          shutil.copyfile('project/' + projectName + '/_mturk.properties', 'project/' + projectName + '/mturk.properties')
          shutil.copyfile('project/' + projectName + '/_mturk.question', 'project/' + projectName + '/mturk.question')
          s2i = details['sample2Info']
          a2l = details['answer2Label']
          s2i = s2i.split('\r\n')
          a2l = a2l.split('\r\n')
          s2i = ['  ' + line for line in s2i]
          a2l = ['  ' + line for line in a2l]
          s2i = '\n'.join(s2i)
          a2l = '\n'.join(a2l)
          with open(EXE_DEF_TEMPLATE) as defTemp:
            details['functions'] = defTemp.read().format(s2i, a2l)
          with open(MC_TEMPLATE) as mcTemp:
            details['mc'] = mcTemp.read()
          with open(AUTO_TEMPLATE) as autoTemp:
            details['auto'] = autoTemp.read()
          with open(CLEAR_MTURK_TEMPLATE) as clearMTurkTemp:
            details['clearMTurk'] = clearMTurkTemp.read()
          
        elif projectStatus['MTurk'] == 'warning':
          details['MTurkDetail'] = '{}'
          with open(EXE_DEF_NULL_TEMPLATE) as defTemp:
            details['functions'] = defTemp.read()
          with open(MC_NULL_TEMPLATE) as mcTemp:
            details['mc'] = mcTemp.read()
          with open(AUTO_NULL_TEMPLATE) as autoTemp:
            details['auto'] = autoTemp.read()
          details['clearMTurk'] = ''
            
        if details['MTurkDetail'] and details['sklearnDetail'] and details['functions']:
          with open(template, 'r') as exeTemp:
            pyContent = exeTemp.read()
            pyContent = pyContent.format(
                           projectName, \
                           details['MTurkDetail'], \
                           details['sklearnDetail'], \
                           details['functions'], \
                           db, \
                           details['mc'], \
                           details['auto'], \
                           details['clearMTurk'])
            with open('project/' + projectName + '/execute.py','w') as exeFile:
              exeFile.write(pyContent)
        
        conn = getDBConnectionFromConfig()[1]
        cur = conn.cursor()
        cur.execute('UPDATE project SET has_changes = 0 WHERE name = %s', (projectName, ))
        conn.commit()
        conn.close()
        s2cMessage('success', 'Execution file is generated successfully')
        logger = Logger(projectName)
        logger.log('success', 'A new execution file is generated successfully.')
        parameter['MTurk'] = projectStatus['MTurk']
        return _render_template('project/execution/execution.html', parameter)
      except Exception, e:
        traceback.print_exc()
        s2cMessage('danger', 'Unexpected error: ' + e.message)
        return redirect('project/' + projectName + '/overview')
    
    #Remove execute.py
    elif 'remove' in request.form:
      if os.path.exists('project/' + projectName + '/execute.py'):
        os.remove('project/' + projectName + '/execute.py')
        s2cMessage('success', 'Execution file is removed.')
      return redirect('project/' + projectName + '/execution')
      
    #Stop the execution
    elif 'stop' in request.form:
      try:
        if isProcessAlive(projectName):
          caProcess[projectName][0].terminate()
          logger = Logger(projectName)
          logger.log('warning', '--------- User terminates the traning process ---------')
          recorder = Recorder(projectName)
          recorder.record(recordType='terminatedAsRequests')
          s2cMessage('warning', 'Training is terminated as user requests.')
          parameter['inExecution'] = False
        return _render_template('project/execution/execution.html', parameter)
      except Exception, e:
        traceback.print_exc()
        s2cMessage('danger', 'Unexpected error: ' + e.message)
        return redirect('project/' + projectName + '/execution')
        
    #Kick off execution
    elif 'execute' in request.form:
      try:
        if isProcessAlive(projectName):
            raise Exception('Application is already in execution.')
        else:          
          #Create thread
          useSandbox = True
          stopAtSampleAmount = 0
          stopAtErrorRate = 0
          projectStatus = checkProjectStatus(projectName)
          
          if projectStatus['MTurk'] == 'ok':
            useSandbox = request.form['useSandbox'] == 'True'
            stopAtErrorRate = request.form['stopAtErrorRate']
            if stopAtErrorRate == '' or stopAtErrorRate is None:
              stopAtErrorRate = None
            else:
              stopAtErrorRate = float(stopAtErrorRate)
            stopAtSampleAmount = int(request.form['stopAtSampleAmount'])
          
          CA = imp.load_source('execute', 'project/' + projectName + '/execute.py')
          t = Process(target=CA.execute, args=(useSandbox, stopAtSampleAmount, stopAtErrorRate))
          caProcess[projectName] = (t, 'training', useSandbox, stopAtErrorRate, stopAtSampleAmount)
          t. start()
          s2cMessage('info', 'Application is running in background. You can monitor it here.')
          parameter['inExecution'] = 'training'
        return redirect('project/' + projectName + '/execution')
      except Exception, e:
        traceback.print_exc()
        s2cMessage('danger', 'Unexpected error: ' + e.message)
        return redirect('project/' + projectName + '/execution')
        
    #Import samples from CSV file
    elif 'importSamples' in request.form:
      try:
        samplesCSV = request.files['samplesCSV']
        conn = getDBConnectionFromConfig()[1]
        cur = conn.cursor()
        header = ('sample', 'feature', 'label', 'for_testing')
        cur.copy_from(file=samplesCSV, null='NULL', table='"' + projectName + '_samples"', columns=header)
        amount = cur.rowcount
        cur.execute('UPDATE "{0}_samples" SET (label_source) = (%s) WHERE label IS NOT NULL'.format(projectName), ('User provided', ))
        conn.commit()
        #User provided
        conn.close()
        logger = Logger(projectName)
        logger.log('success', 'Import of ' + str(amount) + ' samples succeeded')
        s2cMessage('success', 'In total ' + str(amount) + ' samples have been imported.')
        return redirect('project/' + projectName + '/execution')
      except Exception, e:
        traceback.print_exc()
        logger = Logger(projectName)
        logger.log('danger', 'Fail to import samples: ' + e.message)
        s2cMessage('danger', 'Unexpected error: ' + e.message)
        return redirect('project/' + projectName + '/execution')
    else:
      return redirect('project/' + projectName + '/overview')
      
def resetMTurkAccount(projectName):
  parameter = {
    'projectName'         : projectName,
  }
  global caProcess
  try:
    if isProcessAlive(projectName):
      raise Exception('Application is already in execution.')
    else:          
      #Create thread
      useSandbox = True #bool(request.form['useSandbox'])
      if not os.path.exists('project/' + projectName + '/execute.py'):
        raise Exception('A client application generated is required to perform this action.')
      CA = imp.load_source('execute', 'project/' + projectName + '/execute.py')
      t = Process(target=CA.clearMurk, args=(useSandbox, ))
      caProcess[projectName] = (t, 'clearingMTurk')
      t. start()
      s2cMessage('info', 'Operations of clearing MTurk account are executed in background ')
      parameter['inExecution'] = True
    return _render_template('project/remove.html', parameter)
  except Exception, e:
    traceback.print_exc()
    s2cMessage('danger', 'Unexpected error: ' + e.message)
    return redirect('project/' + projectName + '/execution')
      
#Service side create project checking
@mod.route('/_getLogs', methods=['GET'])
def _getLogs(projectName):
  global caProcess
  conn = getDBConnectionFromConfig()
  if conn[0]:
    conn = conn[1]
  else:
    return jsonify(errorMessage=conn[1])
  try:
    is_alive = False
    if projectName in caProcess and caProcess[projectName][0].is_alive():
      is_alive = True
    currentCount = request.args.get('currentCount', 0, type=int)
    cur = conn.cursor()
    cur.execute('''SELECT * FROM "{0}" WHERE log_id > {1} ORDER BY log_id DESC LIMIT 50'''.format(projectName + '_logs', currentCount))
    rows = cur.fetchall()
    amount = len(rows)
    if amount == 0:
      return jsonify(is_alive = is_alive, amount = amount)
    else:
      log_id, log_time, log_type, log_msg = map(list,zip(*rows))
      newCount = log_id[0]
      return jsonify(is_alive = is_alive, amount = amount, newCount = newCount, log_id = log_id, log_time = log_time, log_type = log_type, log_msg = log_msg)
  except Exception, e:
    traceback.print_exc()
    return jsonify(errorMessage='Fail to retrieve logs. ' + e.message)
