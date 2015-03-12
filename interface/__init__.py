from flask import Flask
from views.util import getProjectName

app = Flask(__name__)
app.secret_key = 'cj545124th0aff318041)(&#3y130&$@#!)56160'

from interface.views import general
from interface.views import setup
from interface.views import project
from interface.views import configuration
from interface.views import projectExecution
from interface.views import projectSetting
from interface.views import projectStatistic
app.register_blueprint(general.mod)
app.register_blueprint(setup.mod)
app.register_blueprint(project.mod)
app.register_blueprint(configuration.mod)
app.register_blueprint(projectExecution.mod)
app.register_blueprint(projectSetting.mod)
app.register_blueprint(projectStatistic.mod)

@app.context_processor
def utility_processor():
  def getProjectList():
    return getProjectName()
    
  return dict(getProjectList=getProjectList)
