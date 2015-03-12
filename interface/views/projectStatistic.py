import os, traceback, shutil, math, ast
import numpy as np
from flask import request, Blueprint, jsonify, redirect, url_for
from util import _render_template, getDBConnectionFromConfig, s2cMessage

mod = Blueprint('projectStatistic', __name__, url_prefix='/project/<projectName>/statistic')

@mod.route('/', methods=['GET','POST'])
def statistic(projectName):
  parameter = {
    'projectName'         : projectName,
  }
  return _render_template('project/statistic.html', parameter)
  
@mod.route('/_removeRecords', methods=['GET','POST'])
def _removeRecords(projectName):
  try:
    conn = getDBConnectionFromConfig()[1]
    recordType = request.args.get('recordType', 0, type=str)
    if recordType == "clearAccuracy":
      cur = conn.cursor()
      cur.execute('''TRUNCATE TABLE "{0}" RESTART IDENTITY'''.format(projectName + '_learning_records'))
      conn.commit()
      conn.close()
      return jsonify(msgType = "success", msg = "Accuracy records have been removed.")
    elif recordType == "clearSampleRecord":
      cur = conn.cursor()
      cur.execute('''UPDATE project SET sample_predict = NULL WHERE name = %s''', (projectName, ))
      conn.commit()
      conn.close()
      return jsonify(msgType = "success", msg = "Sample prediction records have been removed.")
    elif recordType == "clearMturkHITRecord":
      cur = conn.cursor()
      cur.execute('''TRUNCATE TABLE "{0}"'''.format(projectName + '_records'))
      conn.commit()
      conn.close()
      return jsonify(msgType = "success", msg = "MTurk HIT records have been removed.")
    else:
      return jsonify(msgType = "danger", msg = "Undefined action.")
  except Exception, e:
    return jsonify(msgType = "danger", msg = "Unexpected error: " + e.message)
  
@mod.route('/_getAccuracyData', methods=['GET','POST'])
def _getAccuracyData(projectName):
  record = []
  try:
    conn = getDBConnectionFromConfig()[1]
    cur = conn.cursor()
    cur.execute('''SELECT * FROM "{0}" WHERE record_type = 'training' ORDER BY time ASC'''.format(projectName + '_learning_records'))
    rows = cur.fetchall()
    record.append({"iteration": 0, "controlGroupSize": 0, "controlGroupAccuracy": 0, "kFoldAccuracy": 0, "deviation": 0, "time": 'Mon, 16 Feb 2015 18:44:01 GMT', "sampleAmount": 0, "payment": 0});
    import time
    for i in range(0, len(rows)):
      record.append({"iteration": i+1, "controlGroupSize": int(rows[i][7]), "controlGroupAccuracy": float(rows[i][8]), "kFoldAccuracy": float(rows[i][9]), "deviation": float(rows[i][10]), "time": rows[i][1], "sampleAmount": int(rows[i][11]), "payment": float(rows[i][12])})
  except:
    record = []
    record.append({"iteration": 0, "controlGroupSize": 0, "controlGroupAccuracy": 0, "kFoldAccuracy": 0, "deviation": 0, "time": 'Mon, 16 Feb 2015 18:44:01 GMT', "sampleAmount": 0, "payment": 0});
  return jsonify(data = record)
  
@mod.route('/_getExecutionMarkers', methods=['GET','POST'])
def _getExecutionMarkers(projectName):
  record = []
  try:
    conn = getDBConnectionFromConfig()[1]
    cur = conn.cursor()
    cur.execute('''SELECT * FROM "{0}" ORDER BY time ASC'''.format(projectName + '_learning_records'))
    rows = cur.fetchall()
    conn.close()
    i = 0;
    for row in rows:
      if row[2] == 'training':
        i = i + 1;
      elif row[2] == 'start':
        record.append({"iteration": i, "time": row[1], "type": row[2], "useSandbox": bool(row[3]), "sklearnSetting": ast.literal_eval(row[6])})
      else:
        record.append({"iteration": i, "type": row[2], "time": row[1]})
  except:
    record = []
  return jsonify(marker = record)
  
  
@mod.route('/_getHITAnsweredRate', methods=['GET','POST'])
def _getHITAnsweredRate(projectName):
  record = []
  try:
    conn = getDBConnectionFromConfig()[1]
    cur = conn.cursor()
    cur.execute("""SELECT count(*) FROM "{0}" WHERE is_expired = true""".format(projectName + '_records'))
    expiredCount = int(cur.fetchall()[0][0])
    cur.execute("""SELECT count(*) FROM "{0}" WHERE is_expired = false""".format(projectName + '_records'))
    answeredCount = int(cur.fetchall()[0][0])
    conn.close()
    total = expiredCount + answeredCount
    if total > 0:
      record.append({
       'description'  : str(answeredCount) + ' HITs are answered by workers within its life time.',
       'rate'        : answeredCount*1.0/total
      })
      record.append({
       'description'  : str(expiredCount) + ' HITs are expired',
       'rate'        : expiredCount*1.0/total
      })
  except:
    record = []
  return jsonify(data = record)
  
@mod.route('/_getHITPendingTime', methods=['GET','POST'])
def _getHITPendingTime(projectName):
  record = []
  try:
    conn = getDBConnectionFromConfig()[1]
    cur = conn.cursor()
    cur.execute("""SELECT accept_time - creation_time FROM "{0}" WHERE is_expired = false""".format(projectName + '_records'))
    rows = cur.fetchall()
    conn.close()
    
    if len(rows) > 0:
      rows = [row[0].total_seconds() for row in rows] #Parse to seconds
      total = len(rows)
      rows = grouping(rows)                           #Grouping according to difference
      rows = futherGrouping(rows, 5)                  #Further hrouping to reduce group number
      record = []
      for row in rows:
        record.append({
         'description'  : str(len(row)) + ' HITs are picked up after <b>' + \
                          str(int(min(row))) + 's</b> to <b>' + str(int(max(row))) + 's</b> after HIT creation.',
         'rate'        : len(row)*1.0/total
        })
  except:
    record = []
  return jsonify(data = record)
  
@mod.route('/_getHITDurationRate', methods=['GET','POST'])
def _getHITDurationRate(projectName):
  record = []
  try:
    conn = getDBConnectionFromConfig()[1]
    cur = conn.cursor()
    cur.execute("""SELECT submit_time - accept_time FROM "{0}" WHERE is_expired = false""".format(projectName + '_records'))
    rows = cur.fetchall()
    conn.close()
    
    if len(rows) > 0:
      rows = [row[0].total_seconds() for row in rows] #Parse to seconds
      total = len(rows)
      rows = grouping(rows)                           #Grouping according to difference
      rows = futherGrouping(rows, 5)                  #Further hrouping to reduce group number
      record = []
      for row in rows:
        record.append({
         'description'  : str(len(row)) + ' HITs are answered within  <b>' + \
                          str(int(min(row))) + 's</b> to <b>' + str(int(max(row))) + 's</b>.',
         'rate'        : len(row)*1.0/total
        })
  except:
    record = []
  return jsonify(data = record)

#Supportive function for radio charts
def grouping(data):
  data.sort()
  diff = [data[i+1]-data[i] for i in range(len(data)-1)]
  avg = sum(diff) / len(diff)
  group = [[data[0]]]
  for x in data[1:]:
      if x - group[-1][-1] < avg:
          group[-1].append(x)
      else:
          group.append([x])
  return group

#Supportive function for radio charts
def futherGrouping(groups, k):
  a_count = np.mean([len(group) for group in groups])
  
  #Grouping tail individuals
  import itertools
  upperQ = np.percentile(list(itertools.chain(*groups)), 75)
  newGroup = []
  while len(groups[len(groups) - 1]) < a_count and np.mean(groups[len(groups) - 1]) > upperQ:
      newGroup.extend(groups.pop(len(groups) - 1))
  if len(newGroup) > 0:
    newGroup.sort()
    groups.append(newGroup)
    
  #Merge small middle individuals
  i = 0
  while i < len(groups)-1:
    if len(groups[i]) < a_count/3:
      diff_before = 0
      if i > 0:
        diff_before = np.mean(groups[i]) - np.mean(groups[i-1])
      diff_after = np.mean(groups[i+1]) - np.mean(groups[i])
      if diff_after > diff_before:
        groups[i] += groups.pop(i+1)
      else:
        groups[i-1] += groups.pop(i)
    i = i+1
  
  #If still too many group, merge to k groups
  while len(groups) > k:
    a = [np.mean(group) for group in groups]
    diff = [a[i+1]-a[i] for i in range(len(a)-1)]
    min_d = min(diff)
    groups[diff.index(min_d)] += groups.pop(diff.index(min_d)+1)
  return groups
    
  
@mod.route('/_getLabelDistribution', methods=['GET','POST'])
def _getLabelDistribution(projectName):
  record = []
  try:
    conn = getDBConnectionFromConfig()[1]
    cur = conn.cursor()
    cur.execute("""SELECT label, count(*) FROM "{0}" WHERE label IS NOT NULL GROUP BY label""".format(projectName + '_samples'))
    rows = cur.fetchall()
    conn.close()
    
    total = 0
    if len(rows) > 0:
      for row in rows:
        total = total + row[1]
      for row in rows:
        record.append({
          'description': str(row[1]) + ' samples have label: <b>' + row[0] + '</b>',
          'rate': row[1]*1.0/total
        })
  except:
    record = []
  return jsonify(data = record)
  
@mod.route('/_getSamplePrediction', methods=['GET','POST'])
def _getSamplePrediction(projectName):
  record = []
  try:
    conn = getDBConnectionFromConfig()[1]
    cur = conn.cursor()
    cur.execute('''SELECT sample_predict FROM project WHERE name = %s''', (projectName,))
    
    rows = cur.fetchall()
    conn.close()
    total = 0
    if len(rows) > 0:
      estimation = ast.literal_eval(rows[0][0])['estimation']
      for e in estimation:
        total = total + e[1]
      for e in estimation:
        record.append({
          'description': str(e[1]) + ' samples have label: <b>' + str(e[0]) + '</b>',
          'rate': e[1]*1.0/total
        })
  except:
    traceback.print_exc()
    record = []
  return jsonify(data = record)

@mod.route('/_getOverallDistribution', methods=['GET','POST'])
def _getOverallDistribution(projectName):
  record = []
  try:
    conn = getDBConnectionFromConfig()[1]
    cur = conn.cursor()
    cur.execute('''SELECT sample_predict FROM project WHERE name = %s''', (projectName,))
    
    rows = cur.fetchall()
    total = 0
    estimation = None
    if len(rows) > 0:
      estimation = ast.literal_eval(rows[0][0])['estimation']
      for e in estimation:
        total = total + e[1]
    estimation = map(list, estimation)
    cur.execute("""SELECT label, count(*) FROM "{0}" WHERE label IS NOT NULL GROUP BY label""".format(projectName + '_samples'))
    rows = cur.fetchall()
    conn.close()
    
    if len(rows) > 0:
      for row in rows:
        total = total + row[1]
      for row in rows:
        for e in estimation:
          if str(row[0]) == str(e[0]):
            e[1] = int(e[1]) + int(row[1])
            break
    
    for e in estimation:
      record.append({
        'description': str(e[1]) + ' samples have label: <b>' + str(e[0]) + '</b>',
        'rate': e[1]*1.0/total
      })
  except:
    traceback.print_exc()
    record = []
  return jsonify(data = record)
