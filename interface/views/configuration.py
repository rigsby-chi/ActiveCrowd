from flask import request, Blueprint
from util import _render_template

mod = Blueprint('configuration', __name__, url_prefix='/configuration')

@mod.route("/", methods=['GET', 'POST'])
def conf():
  return _render_template('general/setup.html')
