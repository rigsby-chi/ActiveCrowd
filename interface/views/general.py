from flask import Flask 
from flask import request, render_template, redirect, url_for, Blueprint
from util import needSetup, _render_template

mod = Blueprint('general', __name__)
  
@mod.route("/", methods=['GET', 'POST'])
def home():
  if request.method == 'GET':
    if not needSetup():
      return _render_template('general/home.html')
    else:
      return _render_template('general/welcome.html')

@mod.route('/about')
def about():
  return _render_template('general/about.html')
