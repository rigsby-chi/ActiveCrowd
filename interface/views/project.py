import os, traceback, shutil, math, ast, pickle
import numpy as np
from flask import request, Blueprint, jsonify, redirect, url_for, Response
from util import _render_template, getDBConnectionFromConfig, s2cMessage
from projectExecution import isProcessAlive, resetMTurkAccount

mod = Blueprint('project', __name__, url_prefix='/project')

@mod.route('/', methods=['GET','POST'])
def project():
  return _render_template('project/createProject.html')

#Project Creation
@mod.route('/create', methods=['GET','POST'])
def createProject():
  if request.method == 'GET':
    return _render_template('project/createProject.html')
  elif request.method == 'POST':
    try:
      #Get database connection
      conn = getDBConnectionFromConfig()[1]
      cur = conn.cursor()
      
      #Get base project infomation and create folder
      projectName=        request.form['projectName']
      projectDescription= request.form['projectDescription']
      if not os.path.exists('project/' + projectName):
        os.makedirs('project/' + projectName)
      
      cur.execute('INSERT INTO project (name, description, useMTurk, sklearnMode) VALUES' + \
                  '(%s, %s, 0, %s) ', (projectName, projectDescription, 'none'))
      cur.execute(open("database/project_create.sql", "r").read().format(projectName))
      conn.commit()
      conn.close()
      
      s2cMessage('success', 'Project is created. ')
      return redirect(url_for('project.overview', projectName=projectName))
    except Exception, e:
      traceback.print_exc()
      s2cMessage('danger', 'Unexpected error: ' + e.message)
      return redirect(url_for('project.createProject'))

#Service side create project checking
@mod.route('/_tryCreateProject', methods=['GET'])
def _tryCreateProject():
  #Get database connection
  conn = getDBConnectionFromConfig()
  if conn[0]:
    conn = conn[1]
  else:
    return jsonify(errorMessage=conn[1])
  try:
    projectName = request.args.get('projectName', 0, type=str)

    #Check project name uniqueness
    cur = conn.cursor()
    cur.execute("""SELECT * FROM project WHERE name=%s""", (projectName,))
    if len(cur.fetchall()) is not 0:
      raise Exception("Project name already in use.")
      
    return jsonify(successMessage = 'Valid project name', \
                   redirect = '/project/'+projectName+'/overview')
  except Exception, e:
    traceback.print_exc()
    return jsonify(errorMessage='Fail to create project. ' + e.message)


@mod.route('/<projectName>/overview', methods=['GET','POST'])
def overview(projectName):
  from util import getProjectDetails
  parameter = getProjectDetails(projectName)
  
  if parameter['sklearnMode'] == 'none':
    s2cMessage('warning', 'You must configure <u><a class="alert-link" href="' + \
                     url_for('projectSetting.sklearn', projectName=projectName)+ \
                     '">SKLearn</a></u> before it can be executed.')
  
  from util import checkProjectStatus
  parameter = dict(parameter.items() + checkProjectStatus(projectName).items())
  
  if parameter['MTurkMsg'] == 'Not configured':
    s2cMessage('warning', 'You must configure <u><a class="alert-link" href="' + \
             url_for('projectSetting.mturk', projectName=projectName)+ \
             '">MTurk</a></u> before it can be executed.')

  return _render_template('project/overview.html', parameter=parameter)
  
  
@mod.route('/<projectName>/logs', methods=['GET', 'POST'])
def fullLogs(projectName): 
  parameter = {
    'projectName'         : projectName,
  }
  if request.method == 'GET':
    return _render_template('project/fullLogs.html', parameter)
  elif request.method == 'POST':
    if 'clearLogs' in request.form:
      try:
        conn = getDBConnectionFromConfig()[1]
        cur = conn.cursor()
        cur.execute('''TRUNCATE TABLE "{0}" RESTART IDENTITY'''.format(projectName + '_logs'))
        conn.commit()
        s2cMessage('success', 'All records are removed.')
      except Exception, e:
        traceback.print_exc()
        s2cMessage('danger', 'Unexpected error: ' + e.message)
    return _render_template('project/fullLogs.html', parameter)
   
@mod.route('/<projectName>/_logs', methods=['GET'])
def _fullLogs(projectName): 
  conn = getDBConnectionFromConfig()[1]
    
  page = request.args.get('page', 1, type=int)
  cur = conn.cursor()
  cur.execute('''SELECT count(*) FROM "{0}"'''.format(projectName + '_logs'))
  totalPage = int(math.ceil(int(cur.fetchall()[0][0])/50.0))
  cur.execute('''SELECT * FROM "{0}" ORDER BY log_id DESC LIMIT 50 OFFSET {1}'''.format(projectName + '_logs', (page-1) * 50))
  rows = cur.fetchall()
  amount = len(rows)
  if amount > 0:
    log_id, log_time, log_type, log_msg = map(list,zip(*rows))
    return jsonify(totalPage = totalPage, amount = amount, log_id = log_id, log_time = log_time, log_type = log_type, log_msg = log_msg)
  else:
    return jsonify(totalPage = totalPage, amount = amount)
    
@mod.route('/<projectName>/samples', methods=['GET','POST'])
def samples(projectName):
  parameter = {
    'projectName'         : projectName,
  }
  return _render_template('project/samples.html', parameter)
  
@mod.route('/<projectName>/_samples', methods=['GET','POST'])
def _samples(projectName):
  conn = getDBConnectionFromConfig()[1]
    
  page = request.args.get('page', 1, type=int)
  cur = conn.cursor()
  labeled = request.args.get('labeled')
  unlabeled = request.args.get('unlabeled')
  top100 = request.args.get('top100')
  where = ' '
  rows = []
  totalPage = 1
  if top100 == 'false':
    if labeled=='true' and not unlabeled=='true':
      where = ' WHERE label IS NOT NULL '
    elif unlabeled=='true' and not labeled=='true':
      where = ' WHERE label IS NULL '
    cur.execute('''SELECT count(*) FROM "{0}" {1}'''.format(projectName + '_samples', where))
    totalPage = int(math.ceil(int(cur.fetchall()[0][0])/100.0))
    cur.execute('''SELECT * FROM "{0}" {1} ORDER BY sample_id ASC LIMIT 100 OFFSET {2}'''.format(projectName + '_samples', where, (page-1) * 100))
    rows = cur.fetchall()
    amount = len(rows)
  elif top100 == 'true':
    cur.execute('''SELECT sample_predict FROM project WHERE name = %s''', (projectName,))
    temp = cur.fetchall()
    top100Id = ast.literal_eval(temp[0][0])['top100']
    for sid in top100Id:
      cur.execute('''SELECT * FROM "{0}" WHERE sample_id = {1}'''.format(projectName+ '_samples', sid))
      temp2 = cur.fetchall()
      rows.append(temp2[0])
      
  amount = len(rows)
  if amount > 0:
    sample_id, sample_s, sample_f, sample_l, sample_ls, sample_c_gp = map(list,zip(*rows))
    return jsonify(totalPage = totalPage, amount = amount, sample_id = sample_id, sample_s = sample_s, sample_f = sample_f, sample_l = sample_l, sample_ls = sample_ls, sample_c_gp = sample_c_gp)
  else:
    return jsonify(totalPage = totalPage, amount = amount)

@mod.route('/<projectName>/_predict', methods=['GET','POST'])
def _predict(projectName):
  sampleId = request.args.get('sampleId', 1, type=int)
  try:
    conn = getDBConnectionFromConfig()[1]
    cur = conn.cursor()
    cur.execute('''SELECT feature FROM "{0}" where sample_id = {1}'''.format(projectName + '_samples', sampleId))
    rows = cur.fetchall()
    if len(rows) == 1:
      with open('project/' + projectName + '/clf.pkl') as clfFile:
        clf = pickle.load(clfFile)
        classes = clf.classes_.tolist()
        p = clf.predict_proba([ast.literal_eval(rows[0][0])])[0].tolist()
        highest = [classes[p.index(max(p))], "%.1f"%(max(p)*100)]
        classes.pop(p.index(max(p)))
        p.pop(p.index(max(p)))
        second = [classes[p.index(max(p))], "%.1f"%(max(p)*100)]
        return jsonify(sampleId = sampleId, h = highest, s = second)
    return jsonify(sampleId = sampleId, h = ['N/A', 'N/A'], s = ['N/A', 'N/A'])
  except:
    return jsonify(sampleId = sampleId, h = ['N/A', 'N/A'], s = ['N/A', 'N/A'])

@mod.route('/<projectName>/export', methods=['GET','POST'])
def export(projectName):
  parameter = {
    'projectName'         : projectName,
    'inExecution'         : isProcessAlive(projectName)
  }
  if request.method == 'GET':
    return _render_template('project/export.html', parameter)
  elif request.method == 'POST':
    from flask import make_response
    
    def returnFile(fileName, fileDisplayName):
      if not os.path.exists('project/' + projectName + '/' + fileName):
        s2cMessage('danger', fileDisplayName + ' not found')
        return _render_template('project/export.html', parameter)
      with open('project/' + projectName + '/' + fileName, 'r') as _file:
        response = make_response(_file.read())
        response.headers["Content-Disposition"] = "attachment; filename=" + projectName + "_" + fileName
        return response

    if 'exportCLF' in request.form:
      return returnFile('clf.pkl', 'Classifer')
      
    elif 'exportPF' in request.form:
      return returnFile('mturk.properties', 'MTurk Properties File')
      
    elif 'exportQF' in request.form:
      return returnFile('mturk.question', 'MTurk Question File')
      
    else:
      s2cMessage('danger', 'Undefined File')
      return _render_template('project/export.html', parameter)
      
@mod.route('/<projectName>/samples.csv', methods=['GET','POST'])
def exportSample(projectName):
  parameter = {
    'projectName'         : projectName,
  }
  if request.method == 'GET':
    return _render_template('project/export.html', parameter)
  elif request.method == 'POST':
    if 'exportS' in request.form:
      conn = getDBConnectionFromConfig()[1]
      cur = conn.cursor()
      rows = None
      WHERE = ''
      if request.form['exportS'] == 'aSamples':
        WHERE = ''
      elif request.form['exportS'] == 'lSamples':
        WHERE = ' WHERE label IS NOT NULL'
      elif request.form['exportS'] == 'uSamples':
        WHERE = ' WHERE label IS NULL'
      else:
        s2cMessage('danger', 'Undefined action')
        return _render_template('project/export.html', parameter)
      cur.execute('''SELECT sample, feature, label, for_testing' FROM "{0}"{1}'''.format(projectName + '_samples', WHERE))
      rows = cur.fetchall()
      csv = ''
      if not len(rows) > 0:
        s2cMessage('danger', 'Requested samples not found')
        return _render_template('project/export.html', parameter)

      def genOutPut(rows):
        for row in rows:
          for_test = '1' if row[3] == True else '0'
          if row[2] is None:
            yield row[0] + '\t' + row[1] + '\t' + 'NULL' + '\t' + for_test + '\n'
          else:
            yield row[0] + '\t' + row[1] + '\t' + str(row[2]) + '\t' + for_test + '\n'
      
      return Response(genOutPut(rows), mimetype='text/csv')
      
    else:
      s2cMessage('danger', 'Undefined File')
      return _render_template('project/export.html', parameter)
   
@mod.route('/<projectName>/remove', methods=['GET','POST'])
def remove(projectName):
  parameter = {
    'projectName'         : projectName,
    'inExecution'         : isProcessAlive(projectName)
  }
  from util import checkProjectStatus
  parameter['MTurk'] = checkProjectStatus(projectName)['MTurk']
  parameter['PYFile'] = checkProjectStatus(projectName)['PYFile']
  if request.method == 'GET':
    return _render_template('project/remove.html', parameter)
  elif request.method == 'POST':
    try:
      removeMode = request.form['selected-remove-mode']
      
      #Remove the whole project
      if removeMode == 'remove-project':
        conn = getDBConnectionFromConfig()[1]
        cur = conn.cursor()
        if os.path.exists('project/' + projectName):
          shutil.rmtree('project/' + projectName)
        cur.execute(open("database/project_remove.sql", "r").read().format(projectName))
        cur.execute(open("database/MTurk_remove.sql", "r").read().format(projectName))
        conn.commit()
        conn.close()
        s2cMessage('success', 'Project ' + projectName + ' has been deleted.')
        return redirect(url_for('general.home'))
      
      elif removeMode == 'remove-labels':
        conn = getDBConnectionFromConfig()[1]
        cur = conn.cursor()
        cur.execute('UPDATE "{0}" SET label = NULL WHERE label IS NOT NULL'.format(projectName + '_samples'))
        amount = cur.rowcount
        conn.commit()
        conn.close()
        s2cMessage('success', 'In total ' + str(amount) + ' labels in project ' + projectName + ' have been deleted.')
        return _render_template('project/remove.html', parameter)
      
      elif removeMode == 'remove-samples':
        conn = getDBConnectionFromConfig()[1]
        cur = conn.cursor()
        cur.execute('DELETE FROM "{0}"'.format(projectName + '_samples'))
        amount = cur.rowcount
        cur.execute('TRUNCATE TABLE "{0}" RESTART IDENTITY'.format(projectName + '_samples'))
        conn.commit()
        conn.close()
        s2cMessage('success', 'In total ' + str(amount) + ' samples in project ' + projectName + ' have been deleted.')
        return _render_template('project/remove.html', parameter)
      
      #Other remove action (not yet implemented)
      elif removeMode == 'remove-HITs':
        return resetMTurkAccount(projectName)
        
      else:
        s2cMessage('danger', 'Undefined action')
        return _render_template('project/remove.html', parameter)
        
    except Exception, e:
      traceback.print_exc()
      s2cMessage('danger', e.message)
      return _render_template('project/remove.html', parameter)
