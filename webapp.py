from flask import Flask, redirect, url_for, session, request, jsonify, Markup
from flask_oauthlib.client import OAuth
#from flask_oauthlib.contrib.apps import github #import to make requests to GitHub's OAuth
from flask import render_template
from datetime import date
from random import randint, randrange

import pymongo
import sys
import pprint
import os
import uuid
import random
import requests
#param = {'post_posted': 1}
#r = requests.get('http://127.0.0.1:5000/get', params=param)
#print(r.status_code)

# This code originally from https://github.com/lepture/flask-oauthlib/blob/master/example/github.py
# Edited by P. Conrad for SPIS 2016 to add getting Client Id and Secret from
# environment variables, so that this will work on Heroku.
# Edited by S. Adams for Designing Software for the Web to add comments and remove flash messaging

app = Flask(__name__)

app.debug = True #Change this to False for production
#os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' #Remove once done debugging

app.secret_key = os.environ['SECRET_KEY'] #used to sign session cookies
oauth = OAuth(app)
oauth.init_app(app) #initialize the app to be able to make requests for user information

#Set up GitHub as OAuth provider
github = oauth.remote_app(
    'github',
    consumer_key=os.environ['GITHUB_CLIENT_ID'], #your web app's "username" for github's OAuth
    consumer_secret=os.environ['GITHUB_CLIENT_SECRET'],#your web app's "password" for github's OAuth
    request_token_params={'scope': 'user:email'}, #request read-only access to the user's email.  For a list of possible scopes, see developer.github.com/apps/building-oauth-apps/scopes-for-oauth-apps
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',  
    authorize_url='https://github.com/login/oauth/authorize' #URL for github's OAuth login
)

connection_string = os.environ["MONGO_CONNECTION_STRING"]
db_name = os.environ["MONGO_DBNAME"]
    
client = pymongo.MongoClient(connection_string)
db = client[db_name]
collection = db['Recipes']

today = date.today()
post = ""

#context processors run before templates are rendered and add variable(s) to the template's context
#context processors must return a dictionary 
#this context processor adds the variable logged_in to the conext for all templates
@app.context_processor
def inject_logged_in():
    return {"logged_in":('github_token' in session)}

@app.route('/')
def home():
    return render_template('home.html')

#redirect to GitHub's OAuth page and confirm callback URL
@app.route('/login')
def login():   
    return github.authorize(callback=url_for('authorized', _external=True, _scheme='http')) #callback URL must match the pre-configured callback URL

@app.route('/logout')
def logout():
    session.clear()
    return render_template('message.html', message='You were logged out')

@app.route('/login/authorized')
def authorized():
    resp = github.authorized_response()
    if resp is None:
        session.clear()
        message = 'Access denied: reason=' + request.args['error'] + ' error=' + request.args['error_description'] + ' full=' + pprint.pformat(request.args)      
    else:
        try:
            session['github_token'] = (resp['access_token'], '') #save the token to prove that the user logged in
            session['user_data']=github.get('user').data
            #pprint.pprint(vars(github['/email']))
            #pprint.pprint(vars(github['api/2/accounts/profile/']))
            message='You were successfully logged in as ' + session['user_data']['login'] + '.'
        except Exception as inst:
            session.clear()
            print(inst)
            message='Unable to login, please try again.  '
    return render_template('message.html', message=message)

@app.route('/forum-created')
def renderCreated():
    print('hello')

@app.route("/create-forum")
def renderForumMaker():
    return render_template("forum_maker.html")

@app.route('/page1', methods = ["POST", 'GET'])
def renderPage1():
    global today
    global post
    global user
    if request.method == 'POST':
        id = random.random()
        make_doc(id, request.form['title'], request.form['contentt'], today.strftime("%m/%d/%y"), session['user_data']['login'])
        for doc in collection.find({'SPECIALID': id}):
            title = doc["Title"]
            user = doc["User"]
            date = doc["Date"]
            content = doc["Content"]
            post = Markup("<br> \n<div class='card add'> \n\t<div class='card-header'>\n\t\t<h4 class='card-title'>"+title+"</h4> \n\t\t<span class='card-text'>"+user+"</span> \n\t\t<span class='card-text right'>"+str(date)+"</span> \n\t</div> \n\t<div class='card-body'> \n\t\t<p class='card-body'>"+content+"</p> \n\t</div> \n\r</div>") + post
        return render_template('page1.html', posts = post)
    return render_template('page1.html')

@app.route('/page2')
def renderPage2():
    return render_template('page2.html')

@app.route('/googleb4c3aeedcc2dd103.html')
def render_google_verification():
    return render_template('googleb4c3aeedcc2dd103.html')

#the tokengetter is automatically called to check who is logged in.
@github.tokengetter
def get_github_oauth_token():
    return session['github_token']

def make_doc(id, title, content, date, user):
    doc = {'SPECIALID': id, "Title": title, "User": user, "Date": date, "Content": content}
    collection.insert_one(doc)

if __name__ == '__main__':
    app.run()