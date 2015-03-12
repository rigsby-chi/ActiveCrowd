from flask import request, Blueprint, jsonify
from util import getRelativePath, _render_template, getDBConnection
import json, psycopg2, traceback

mod = Blueprint('setup', __name__, url_prefix='/setup')


@mod.route("/", methods=['GET', 'POST'])
def setup():
  if request.method == 'GET':
    return _render_template('general/setup.html')

@mod.route('/_trySetup')
def _trySetup():
  DBName = request.args.get('DBName', 0, type=str)
  DBUser = request.args.get('DBUser', 0, type=str)
  DBPassword = request.args.get('DBPassword', 0, type=str)
  AWSKey = request.args.get('AWSKey', 0, type=str)
  AWSSecretKey = request.args.get('AWSSecretKey', 0, type=str)

  conn = getDBConnection(DBName, DBUser, DBPassword)
  if conn[0]:
    conn = conn[1]
  else:
    return jsonify(errorMessage=conn[1])
  
  try:
    cur = conn.cursor()
    cur.execute(open("database/setup.sql", "r").read())
    conn.commit()
    
    config = {
                "DBName": DBName, 
                "DBUser": DBUser,
                "DBPassword": DBPassword,
                "AWSKey": AWSKey,
                "AWSSecretKey": AWSSecretKey
             }
    with open(getRelativePath('config.json'), 'wb') as config_file:
      json.dump(config, config_file)
    conn.close()
    return jsonify(successMessage = 'You will be redirect to home page soon.', redirect = '/')
  except:
    conn.close()
    traceback.print_exc()
    return jsonify(errorMessage='Fail to connect to database with provided details.')
   
