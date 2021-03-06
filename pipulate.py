"""                         Because life's too short to not collect  ABOUT THE AUTHOR:                                    1
                            data in the same place you work with it  http://mikelev.in                                    2
                                                                     http://levinux.com                                   3
                             _____ _             _       _           http://pipulate.com                                  |
                            |  __ (_)           | |     | |          
                            | |__) | _ __  _   _| | __ _| |_ ___    ___ ___  _ __ ___                                     V
                            |  ___/ | '_ \| | | | |/ _` | __/ _ \  / __/ _ \| '_ ` _ \
                            | |   | | |_) | |_| | | (_| | ||  __/ | (_| (_) | | | | | |
                            |_|   |_| .__/ \__,_|_|\__,_|\__\___|(_)___\___/|_| |_| |_|
                                    | |
                               THIS |IS YOUR BROWSER
                                    | |
                      THIS IS      \` `/                               THIS IS PIPULATE
                        YOU         \ / ___ ____                     (disposable servers)
                                   ,_V_/site\___\___. ...which       ,------------------.
                         O         |                ||    SENDS      |   ...to the      |
                        /|\---1.-----> bookmarklet ----------2.-------> Pipulate Server |
                        ( ) CLICK  | with a website ||      URL and  |   | which checks |
                       =====       |   displaying.  ||       context '---|---|--|--|----'
                         |         |                ||                   |   |  |  |
                         5.        '----------------'|      then sends   |   |  |  '-------> ?
                       SEE THE--->  | to Google Sheet|<-------4.---------'   |  '----3.----> ?
                       RESULTS      '----------------'  a response           '-------------> ?
                                                                            ...stuff on net


# THE PIPULATE TO-DO LIST:
- Support this library https://github.com/google/oauth2client
- Get rid of annoying timeouts making you log back in, and potentially interrupting jobs!
- Get rid of the stormy weather messaging, and just figure out how to do exponential back-off (never stop on API hiccups)
- Switch login technique to OAuth-persistent (offline app)
- Port to Python 3
- Incorporate Splash or Mechanize for headless browsing.
- nginx load balancer on Wable network (or something node?)
- Break off 2 Rackspace pipulate instances
- Dyamically importing user functions
- Email Support
- Support yield from and decorators
- Consider forking threads that don't stream I/O to browser
- Also support https://cse.google.com/cse/ and main UI scraping for serps
- Accessing and saving-local Google Webmaster Tools data.
- Google Analytics API
- Saving Google search results (both for SERPS and non-SERPS purposes)
- Calculate relative "difficulty" scores among fixed data sets

"""

#  _                            _     _   _     _       While it may look it, this is not the entry-point for Pipulate.
# (_)_ __ ___  _ __   ___  _ __| |_  | |_| |__ (_)___   Both webpipulate.py (the Flask context) and loopipulate.py (the
# | | '_ ` _ \| '_ \ / _ \| '__| __| | __| '_ \| / __|  command-line context for cron) import this file as one of their
# | | | | | | | |_) | (_) | |  | |_  | |_| | | | \__ \  first steps. It does it with "from pipulate import *" so that
# |_|_| |_| |_| .__/ \___/|_|   \__|  \__|_| |_|_|___/  everything here is running in top-level scope. The next few lines
#             |_|                                       are most of the early-load ubiquitous libraries used throughout.

import sys, os, socket, urlparse, re, gspread
import requests, traceback, datetime, time, json
import globs
from common import *
from flask import (Flask,
                  stream_with_context,
                  render_template,
                  Response,
                  request,
                  session,
                  redirect,
                  url_for,
                  flash)
# from functions import *

#                          _          __  __    This ain't PHP. It's kinda like a .NET codebehind, but way more awesome
#   __ _ _ __  _ __    ___| |_ _   _ / _|/ _|   because it's Python. But Python resisting doing things like plugging whole
#  / _` | '_ \| '_ \  / __| __| | | | |_| |_    high-level frameworks in the core product relies on 3rd party developers
# | (_| | |_) | |_) | \__ \ |_| |_| |  _|  _|   to fill the void--and in this case, it happens to be Flask. And Flask
#  \__,_| .__/| .__/  |___/\__|\__,_|_| |_|     happens to be Werkzeug to handle "web routing" and Jinja2 to handle
#       |_|   |_|                               PHP-style web templates. It takes time to grok, but is worth it.
#
socket.setdefaulttimeout(10.0)

app = Flask(__name__) #                         <-- This is a rather big moment in this application's lifecycle.
if (os.path.isfile(globs.FILE) and
      os.path.getsize(globs.FILE) > 0):
    app.config.from_pyfile(globs.FILE, silent=False)
    app.config['SESSION_TYPE'] = 'filesystem'   # Ensures secret is always set for first page-load after server restart.

def stream_template(template_name, **context):  # There's a rather awesome bit of Python magic going on here. This is
  """Open inexpensive Flask-based streaming.""" # essentially a replacement for render_template() but which repeatedly
  app.update_template_context(context)          # "flushes" streaming output to the user. Part of the context expected
  t = app.jinja_env.get_template(template_name) # is data=somegeneratorinstance. Something inside a Flask object are
  rv = t.stream(context)                        # instructions what to do if it gets a generator object on a parameter
  return rv                                     # named data. And THIS is how the entire app is kept so lightweight.

@app.context_processor
def templateglobals():
  """Make functions usable in templates."""
  alink = ''
  if session:
    alink = getLoginlink()
  hostname = socket.gethostname()
  if hostname[-8:] == 'pipulate':
    hostname = hostname[:-8]
  return dict(loginlink=alink,
  bookmarklet=getBookmarklet(),
  blabel=getLabel(),
  logoutlink=getLogoutlink(),
  cyclemotto=cyclemotto(),
  hostname=hostname
  )

from managelists import *

@app.route("/update")
def update():
  import subprocess
  if request.args and 'all' in request.args:
    msg = '<ol>\n'
    for ahost in ['prod', 'newyork', 'dallas', 'seattle']:
      aurl = 'http://%s.pipulate.com/update' % ahost
      rtext = requests.get(aurl, timeout=10).text
      rtext = rtext.replace('\n', '<br/>\n')
      msg = msg + "<li>%s: %s</li>\n" % (ahost, rtext)
    msg = msg + "</ol>\n"
    msg2 = '''<html>
      <head>
        <title>Updating all servers</title>
      </head>
      <body>
        <h1>Updating all servers</h1>
        %s
      </body>
    </html>''' % msg
    return render_template('update.html', output=msg2)
  else:
    process = subprocess.Popen("/usr/bin/git pull", cwd="/var/pipulate/", shell=True, stdout=subprocess.PIPE)
    output = process.communicate()[0]
    return render_template('update.html', output=output)

@app.route("/v")
def visualize():
  if session and 'oa2' in session:
    out("Session")
    creds = Credentials(access_token=session['oa2'])
    gsp = gspread.authorize(creds)
    try:
      gdoc = gsp.open_by_key(request.args['k'])
    except:
      return redirect(url_for('main'))
    vsheet = gdoc.worksheet("visualizations")
    vkey = request.args['v']
    vrow = vsheet.find(vkey).row
    vcols = vsheet.row_values(1)
    darow = vsheet.row_values(vrow)
    idex = vcols.index('includecode')
    cdex = vcols.index('compresseddata')
    return render_template('visualize.html', injectjson=unarchive(darow[cdex]), injectincludes=darow[idex])
  else:
    return redirect(url_for('main'))

#  _   _                                              Flask uses a routing system from another package called Werkzeug.
# | | | | ___  _ __ ___   ___ _ __   __ _  __ _  ___  Werkzeug uses decorators to "route" requests. You can read the main
# | |_| |/ _ \| '_ ` _ \ / _ \ '_ \ / _` |/ _` |/ _ \ function as: Feed the entire main() function as a parameter to the
# |  _  | (_) | | | | | |  __/ |_) | (_| | (_| |  __/ route method of the Flask app object, keeping all of Flask's "outer"
# |_| |_|\___/|_| |_| |_|\___| .__/ \__,_|\__, |\___| conext, which happens to be everying you need for a standard Python
#                            |_|          |___/       WSGI webserver. There's no Apache, nginx or even gunicorn here.
@app.route("/", methods=['GET', 'POST'])
def main():
  """Ensures config and login requirements met."""
  print('''
               ____  _             _       _   _
              |  _ \(_)_ __  _   _| | __ _| |_(_)_ __   __ _
              | |_) | | '_ \| | | | |/ _` | __| | '_ \ / _` |
              |  __/| | |_) | |_| | | (_| | |_| | | | | (_| |  _   _   _
              |_|   |_| .__/ \__,_|_|\__,_|\__|_|_| |_|\__, | (_) (_) (_)
                      |_|                              |___/
  ''')
  out("ENTERED MAIN FUNCTION", "0")
  stop = False
  streamit = False
  readytopip = False
  form = PipForm(csrf_enabled=False)
  formDict = secondaryMenu()
  form2 = None
  if 'Host' in request.headers:
    globs.HOST = request.headers['Host']
  if ':' in form.options.data:
    form2 = formDict[form.options.data.split(':')[1]]
  else:
    form2 = PipForm2(csrf_enabled=False)
  if (request.method == 'POST'
      and 'secondary' in form2
      and form2.secondary.data == 'on'):
    form2 = formDict[form.options.data.split(':')[1]]
  menudefault = None
  selectedtext = None
  configform = ConfigForm(csrf_enabled=False)
  if (os.path.isfile(globs.FILE) and
      os.path.getsize(globs.FILE) > 0):
    app.config.from_pyfile(globs.FILE, silent=False)
    app.config['SESSION_TYPE'] = 'filesystem'
  else:
    #                                                   ____        # This traps the first time Pipulate is run on a new
    #   ___  ___ _ ____   _____ _ __    ___ ___  _ __  / _(_) __ _  # server and prompts you to enter your Google Developer
    #  / __|/ _ \ '__\ \ / / _ \ '__|  / __/ _ \| '_ \| |_| |/ _` | # Web app OAuth2 Client ID and Secret that you get from
    #  \__ \  __/ |   \ V /  __/ |    | (_| (_) | | | |  _| | (_| | # https://console.developers.google.com/project so that
    #  |___/\___|_|    \_/ \___|_|     \___\___/|_| |_|_| |_|\__, | # You never need to keep your username and password on
    #                                                        |___/  # the hard drive. In fact now, you can't anymore.
    if request.method == 'POST':
      import pickle
      pickleme = {
        'CLIENT_ID': configform.clientid.data,
        'CLIENT_SECRET': configform.clientsecret.data,
        'APP_SECRET': configform.appsecret.data
      }
      pickle.dump(pickleme, open(globs.TOKEN, 'wb'))
      redir = 'http://'+globs.HOST
      scope = 'https://spreadsheets.google.com/feeds/'
      if globs.PCOM:
        scope = 'profile email ' + scope
      qsdict = {  'scope': scope,
                  'response_type': 'code',
                  'access_type': 'offline',
                  'redirect_uri': redir,
                  'approval_prompt': 'force',
                  'client_id': configform.clientid.data
                }
      from urllib import urlencode
      linktologin = "%s?%s" % (globs.OAUTHURL, urlencode(qsdict))
      return redirect(linktologin)
    elif request.args and 'code' in request.args:                   # Trap condition where "code" is found in querystring
      code = request.args['code']
      scope = 'https://spreadsheets.google.com/feeds/'
      redir = 'http://'+globs.HOST
      endpoint = "https://www.googleapis.com/oauth2/v3/token" # Notice the new endpoint for this exchange.
      import pickle
      writeus = pickle.load(open(globs.TOKEN, "rb"))
      postheaders = {
        'client_id': writeus['CLIENT_ID'],
        'client_secret': writeus['CLIENT_SECRET'],
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': redir
        } # Construct POST header values for exchanging initial OAuth2 code for refresh and access tokens.
      r = requests.post(endpoint, postheaders)
      rd = r.json()
      output = open(globs.FILE, 'wb') # Copy temporarily pickled values to permanent Flask server config file.
      output.write("CLIENT_ID = '%s'\n" % writeus['CLIENT_ID'])
      output.write("CLIENT_SECRET = '%s'\n" % writeus['CLIENT_SECRET'])
      output.write("SECRET_KEY = '%s'\n" % writeus['APP_SECRET'])
      output.write("REFRESH_TOKEN = '%s'\n" % rd['refresh_token'])
      output.close()
      from datetime import datetime, timedelta
      xseconds = rd['expires_in']
      expiresin = datetime.now() + timedelta(seconds=xseconds)
      pickleme = {
        'access_token': rd['access_token'],
        'expires': expiresin
      }
      pickle.dump(pickleme, open(globs.TOKEN, 'wb')) # Pickle the frequenlty-changed access token
      return render_template('pipulate.html') # Get "code" out of the URL.
    else: # Config file not found, nor POST method or "code" on querystring.
      return render_template('pipulate.html', configform=configform) # Start server configuration procedure.
  if session and 'oa2' in session: # Appears that user is logged in already.
    #                    _            _   _       _
    #   ___ _ __ ___  __| | ___ _ __ | |_(_) __ _| |___
    #  / __| '__/ _ \/ _` |/ _ \ '_ \| __| |/ _` | / __|
    # | (__| | |  __/ (_| |  __/ | | | |_| | (_| | \__ \
    #  \___|_|  \___|\__,_|\___|_| |_|\__|_|\__,_|_|___/
    #
    session.permanent = True
    creds = Credentials(access_token=session['oa2'])
    try:
      gsp = gspread.authorize(creds)
      gsp.openall()
      session['loggedin'] = "1"
    except:
      session.pop('loggedin', None)
    #      _                  _             _   Yes, Pipulate needs to know what spreadsheet to target,
    #  ___| |_ ___  _ __  ___(_) __ _ _ __ | |  and making a new one every time is a terrible mess.
    # / __| __/ _ \| '_ \/ __| |/ _` | '_ \| |  Been there, done that. And so, it ALWAYS targets a sheet
    # \__ \ || (_) | |_) \__ \ | (_| | | | |_|  named Pipulate unless you click the bookmarklet FROM a
    # |___/\__\___/| .__/|___/_|\__, |_| |_(_)  Google Sheet. Then, it targets that. In any case, this
    #              |_|          |___/           version is great at recycling and reducing file cruft.
    if session and 'loggedin' in session and session['loggedin'] == "1":
      needsPipulate = True
      tasteMe = None
      if request.args and 'u' in request.args and globs.SHEETS in request.args.get('u'):
        needsPipulate = False
        tasteMe = request.args.get('u')
      elif request.args and 'u' in request.args and globs.SHEETS not in request.args.get('u'):
        needsPipulate = False
        menudefault = 'client'
      elif request.method == 'POST':
        needsPipulate = False
      if tasteMe:
        gdoc = gsp.open_by_url(tasteMe)
      else:
        out("Attempting to load %s sheet." % globs.NAME)
        try:
          gdoc = gsp.open(globs.NAME)
        except:
          pass
      try:
        globs.DOCID = gdoc.id
        globs.NAME = gdoc.title
        globs.TAB = gdoc.sheet1.title
        globs.sheet = gdoc.sheet1
        globs.worksheets = gdoc.worksheets()
        globs.tabnames = [sheet.title for sheet in globs.worksheets]
        needsPipulate = False
        out("Loaded %s sheet." % gdoc.title)
      except:
        pass
      try:
        gdoc.sheet1.find('?')
        readytopip = True
        if not menudefault:
          menudefault = "qmarks"
      except:
        pass
      # Indoctrinate new Pipulate users here
      if request.args and 'logout' in request.args:
        pass
      elif request.args and 'code' in request.args:
        pass
      elif needsPipulate and 'access_token' not in request.args:
        out("EXITING MAIN FUNCTION RENDER INDOCTRINATE", "0", '-')
        return render_template('pipulate.html', form=form, select=None)
  globs.DOCLINK = '<b><a href="%s/d/%s/edit#gid=0" target="_blank">%s<i class="pip-icon pip-link-ext"></i></a></b>' % (globs.SHEETS, globs.DOCID, globs.NAME)
  menutwo = False
  if request.method == 'POST':
    #  ____   ___  ____ _____   ____  _                              _   Shazam! is the block in which we create the
    # |  _ \ / _ \/ ___|_   _| / ___|| |__   __ _ ______ _ _ __ ___ | |  first instance of the Pipulate() generator
    # | |_) | | | \___ \ | |   \___ \| '_ \ / _` |_  / _` | '_ ` _ \| |  object that gets called again later as the
    # |  __/| |_| |___) || |    ___) | | | | (_| |/ / (_| | | | | | |_|  data paramater of a stream_template() call
    # |_|    \___/|____/ |_|   |____/|_| |_|\__,_/___\__,_|_| |_| |_(_)  enabling our magic streaming output. Shazam!
    #
    if form and 'options' in form and form.options.data == 'repipulate':
      streamit = stream_with_context(prePipulators()['repipulate']())
    elif form and 'options' in form and form.options.data == 'client':
      streamit = stream_with_context(prePipulators()['client']())
    elif form2 and 'secondary' in form2 and form2.secondary.data == 'on':
      menutwo = True
      psKey = globs.MODE
      if 'radios' in form2:
        psKey = form2.radios.data
      elif 'checks' in form2:
        checklist = form2.checks.data
        psKey = checklist[0]
        for item in checklist:
          if ':' in item:
            psKey = item.split(':')[0]
            break
      if ':' in psKey:
        psKey = globs.MODE.split(':')[1]
      if psKey == 'cancel':
        return redirect(url_for('main', u=form2.pipurl.data))
      if psKey == 'add':
        checks = None
        try:
          checks = form2.checks.data
        except:
          pass
        if checks:
          streamit = stream_with_context(prePipulators()[psKey](checks))
        else:
          streamit = stream_with_context(prePipulators()[psKey]())
      else:
        streamit = stream_with_context(prePipulators()[psKey]())
    elif form.pipurl.data:
      globs.PIPURL = form.pipurl.data
      if form.options.data:
        globs.MODE = form.options.data
        if ':' in globs.MODE:
          mode = globs.MODE.split(':')[1]
          return render_template('pipulate.html', form=form, form2=form2, mode=mode)
      if form.magicbox.data:
        globs.KEYWORDS = form.magicbox.data
        form.magicbox.data = None
      streamit = stream_with_context(repipulate())
    else:
      flash('Please enter a URL to Pipulate.')
  else:
    #  ___                                _        _              You're here because method doesn't equal POST.
    # |__ \__ _ _   _  ___ _ __ _   _ ___| |_ _ __(_)_ __   __ _  It's a very important place to be, because
    #   / / _` | | | |/ _ \ '__| | | / __| __| '__| | '_ \ / _` | data passed on the URL is a super-reliable way
    #  |_| (_| | |_| |  __/ |  | |_| \__ \ |_| |  | | | | | (_| | to pass data between systems, sessions, or
    #  (_)\__, |\__,_|\___|_|   \__, |___/\__|_|  |_|_| |_|\__, | what have you. That's why you'll see logout
    #        |_|                |___/                      |___/  handling and client-to-server data handoffs.
    if request.args:
      if 's' in request.args:
        form.magicbox.data = request.args.get('s')
        selectedtext = request.args.get('s')
      if 'access_token' in request.args: # Oops... necessary evil. Redirect quickly.
        try:
          LogUser(request.args['access_token'])
        except:
          pass
        try:
          session['oa2'] = request.args.get("access_token")
          session['loggedin'] = "1"
        except:
          pass
        try:
          session['i'] -= 1 # Don't skip a cute message, just becuse I redirect.
        except:
          pass
        if 'u' in session and 's' in session:
          out("EXITING MAIN FUNCTION REDIRECT WITH URL AND TEXT", "0", '-')
          #return redirect(url_for('main', u=session['u'], s=session['s'], l='1'))
          return redirect(url_for('main', u=session['u'], s=session['s']))
        elif 'u' in session:
          out("EXITING MAIN FUNCTION REDIRECT WITH URL", "0", '-')
          #return redirect(url_for('main', u=session['u'], l='1'))
          return redirect(url_for('main', u=session['u']))
        else:
          out("Redirecting, no URL known")
          out("EXITING MAIN FUNCTION REDIRECT", "0", '-')
          #return redirect(url_for('main', l='1'))
          return redirect(url_for('main'))
      elif 'logout' in request.args: # Logging out
        if session:
          if 'oa2' in session:
            revokeurl = 'https://accounts.google.com/o/oauth2/revoke?token=' + session['oa2']
            requests.get(revokeurl, timeout=5)
          if 'u' in request.args:
            form.pipurl.data = request.args.get('u')
            globs.PIPURL = request.args.get('u')
          session.pop('loggedin', None)
      else: # Move selected text and current url into session object.
        try:
          if 's' in request.args:
            session['s'] = request.args.get('s')
          if 'u' in request.args:
            form.pipurl.data = request.args.get('u')
            globs.PIPURL = request.args.get('u')
            session['u'] = request.args.get('u')
          # Taken out to prevent "misfires"
          #if session and 'u' in session:
          #  form.pipurl.data = session['u']
          #  globs.PIPURL = session['u']
        except:
          pass
  #    ____ _____ _____                                                   What better place to "GET" messages than
  #   / ___| ____|_   _|  _ __ ___   ___  ___ ___  __ _  __ _  ___  ___   where the GET method is being used to build
  #  | |  _|  _|   | |   | '_ ` _ \ / _ \/ __/ __|/ _` |/ _` |/ _ \/ __|  the normally much more stream-y UI. But it's
  #  | |_| | |___  | |   | | | | | |  __/\__ \__ \ (_| | (_| |  __/\__ \  not needed, and Flask provides yet another
  #   \____|_____| |_|   |_| |_| |_|\___||___/___/\__,_|\__, |\___||___/  thing for the world flash to mean. Nice little
  #                                                     |___/             higher abstraction doohickey in Flask framework.
  menuTupleList = mainMenu()

  if request.method == 'GET':
    if menutwo:
      pass
    elif selectedtext and globs.SHEETS not in globs.PIPURL:
      menudefault = "keywords"
      session.pop('_flashes', None)
      flash("Words highlighted. Preparing to harvest keywords.")
      flash("Insert commas between keywords, and each one will get its own row.")
      flash("You can also add more keyword variations by just typing them in.")
      flash('Select "Harvest Keywords" from the dropdown menu.')
    else:
      session.pop('_flashes', None)
      flash('This targets %s in your Google sheet named %s' % (globs.TAB, globs.DOCLINK))
      if readytopip:
        flash('Everything seems set up properly. Click button to proceed.')
      #elif globs.sheet.row_values(1)==[] and globs.sheet.row_values(2) == []:
      #  flash('If you are new to Pipulate, watch the demo.')
      else:
        flash("It appears %s has no queston marks." % globs.TAB)
        flash("warning")
        if 'Config' not in globs.tabnames:
          menuTupleList = [('qmarks'      , "Initialize Sheet")] + menuTupleList
  options = '<option value="off">What do you want to do?</option>\n'
  for item in menuTupleList:
    options += '<option value="%s">%s</options>\n' % (item[0], item[1])

  out("Selecting template method.")
  #  _                       _       _              To Stream or to Render, that is the question. 'Tis it not nobler
  # | |_ ___ _ __ ___  _ __ | | __ _| |_ ___  ___   to embrace the streamy render_temblate alternative in Flask and
  # | __/ _ \ '_ ` _ \| '_ \| |/ _` | __/ _ \/ __|  do all the ajaxy-communication tight on the same response that
  # | ||  __/ | | | | | |_) | | (_| | ||  __/\__ \  built the form in the first place? How little overhead. How few
  #  \__\___|_| |_| |_| .__/|_|\__,_|\__\___||___/  parts. How adaptable to unimaginably diverse situations in the
  #                   |_|                           future! Flask-SocketIO is not ruled it. It is just not necessary.
  if streamit:
    #Handle streaming user interface updates resulting from a POST method call.
    return Response(stream_template('pipulate.html', form=form, select=options, data=streamit)) # <-- Look Closely!!!
  else:
    #Handle non-streaming user interface build resulting from a GET method call.
    out("EXITING MAIN FUNCTION RENDER", "0", '-')
    return render_template('pipulate.html', form=form, select=options, menudefault=menudefault)
  out("EXITING MAIN", "0", '-')

def LogUser(authkey):
  """Track usage of the Pipulate bookmarklet per user on main domain instance."""
  #  _                _   _
  # | |    ___   __ _| | | |___  ___ _ __
  # | |   / _ \ / _` | | | / __|/ _ \ '__|
  # | |__| (_) | (_| | |_| \__ \  __/ |
  # |_____\___/ \__, |\___/|___/\___|_|
  #             |___/
  import os.path
  if os.path.isfile(globs.TOKEN) and os.path.getsize(globs.TOKEN) > 0:
    token = freshtoken(globs.TOKEN)
    creds = Credentials(access_token=token)
    import gspread
    gsp2 = gspread.authorize(creds)
    api = 'https://www.googleapis.com/oauth2/v1/userinfo?alt=json&access_token='
    api = api + authkey
    ujson = requests.get(api, timeout=5)
    adict = ujson.json()
    try:
      usersheet = gsp2.open("Users").sheet1
      emails = usersheet.col_values(1)
    except:
      return
    email = ''
    if "email" in adict:
      email = adict["email"].lower()
    if email in emails:
      emaildex = emails.index(email) + 1
      userange = 'H%s:I%s' % (emaildex, emaildex)
      try:
        CellList = usersheet.range(userange)
        CellList[0].value = timestamp()
        CellList[1].value = str(int(CellList[1].value) + 1)
        usersheet.update_cells(CellList)
      except:
        return
    else:
      user = []
      if 'email' in adict:
        user.append(adict["email"].lower())
      else:
        return
      for item in ['name', 'link', 'locale', 'gender', 'id']:
        try:
          user.append(adict[item])
        except:
          user.append('')
      user.append(timestamp())
      user.append('')
      user.append('1')
      try:
        InsertRows(usersheet, [user], len(emails))
      except:
        return
  else:
    out("%s not found. Run python configure.py" % globs.FILE)
#  __  __                   _ _ _   _     _         ____                           _              I am a monolith until I
# |  \/  | ___  _ __   ___ | (_) |_| |__ (_) ___   / ___| ___ _ __   ___ _ __ __ _| |_ ___  _ __  fuse my defensive api
# | |\/| |/ _ \| '_ \ / _ \| | | __| '_ \| |/ __| | |  _ / _ \ '_ \ / _ \ '__/ _` | __/ _ \| '__| coding trick with my
# | |  | | (_) | | | | (_) | | | |_| | | | | (__  | |_| |  __/ | | |  __/ | | (_| | || (_) | |    streaming user output
# |_|  |_|\___/|_| |_|\___/|_|_|\__|_| |_|_|\___|  \____|\___|_| |_|\___|_|  \__,_|\__\___/|_|    trick. You may not get
#                                                                                                 it, but you will yield.
def Pipulate(preproc='', dockey='', targettab="", token='', label='', determined=False):
  """Generator that streams output to a web user interface."""
  stop = False
  qset = set()
  qstart = 1
  qend = 1
  badtuple = (globs.GBAD, globs.GBAD, "", "")
  flush = ("", "", "", "")
  lock = ("", "", "", "+")
  unlock = ("", "", "", "-")
  stopit = ("stop", "", "", "")
  spinerr = "spinerr", "", "", ""
  spinoff = "spinoff", "", "", ""
  warning = ("warning", "", "", "")
  finished = ("finished", "", "", "")
  success = ("success", "", "", "")
  out("PIPULATION BEGINNING", "1")
  if label:
    yme = '<span class="labelhead">%s</span>' % label
    yield yme, label, "", ""
    yield "piplogo", "", "", ""
  #                                            _     _         _                Try to keep your try blocks small to isolate where the
  #   ___  _ __   ___  __   _____ _ __ _   _  | |__ (_) __ _  | |_ _ __ _   _   errors are coming from. Or do this. Python is a very
  #  / _ \| '_ \ / _ \ \ \ / / _ \ '__| | | | | '_ \| |/ _` | | __| '__| | | |  pragmatic language, and sometimes you have to take
  # | (_) | | | |  __/  \ V /  __/ |  | |_| | | |_) | | (_| | | |_| |  | |_| |  advantage of how try/exept can work in a big generotor
  #  \___/|_| |_|\___|   \_/ \___|_|   \__, | |_.__/|_|\__, |  \__|_|   \__, |  yielding instructions to a Web browser UI, which must
  #                                    |___/           |___/            |___/   be told in its final dying breath to stop spinning.
  try:
    #if globs.WEB:
    #  yield "Beginning to Pipulate! Opening sheet...", "", "", ""
    #  yield "spinon", "", "", ""
    out("Reading in functions.")
    funcs = [x for x in globals().keys() if x[:2] != '__'] #List all functions
    transfuncs = ziplckey(funcs, funcs) #Keep translation table
    blankrows = 0
    gsp = None
    gdoc = None
    stop = True
    gfuncs = [x.lower() for x in globals().keys() if x[:2] != '__']
    scrapers = [x[0].lower() for x in scrapes()]
    globs.funcscrapes = set(gfuncs + scrapers)
    if session or (dockey and token):
      out("LOGIN ATTEMPT", "2")
      sheet = ''
      cell = None
      if dockey and token:
        creds = Credentials(access_token=token)
        gsp = gspread.authorize(creds)
        gdoc = gsp.open_by_key(dockey)
      else:
        if 'oa2' in session:
          creds = Credentials(access_token=session['oa2'])
          out("Credential object created.")
        else:
          out("Expired login.")
          if globs.WEB:
            yield "Google Login expired. Log back in.", "Login under the \"burger button\" in the upper-right.", "", ""
            yield spinoff
        try:
          gsp = gspread.authorize(creds)
        except:
          out("Login failed.")
          if globs.WEB:
            yield "Google Login unsuccessful.", "", "", ""
            yield spinoff
          raise StopIteration
        else:
          out("Login successful.")
        out("Opening Spreadsheet...")
        stop = True
        for x in range(10):
          if globs.WEB: yield lock
          try:
            gdoc = gsp.open_by_url(globs.PIPURL)
            globs.DOCID = gdoc.id
            globs.NAME = gdoc.title
            if targettab:
              globs.TAB = gdoc.worksheet(targettab).title
            else:
              globs.TAB = gdoc.sheet1.title
            globs.sheet = gdoc.worksheet(globs.TAB)
            stop = False
            break
          except gspread.httpsession.HTTPError, e:
            out("Login appeared successful, but rejected on document open attempt.")
            yme = 'Please <a href="%s">Log In</a> again first.' % getLoginlink()
            if globs.WEB:
              yield yme, "Login under the \"burger button\" in the upper-right.", "", ""
              yield warning
              yield flush
            if session and 'loggedin' in session:
              session.pop('loggedin', None)
            if 'u' not in session and globs.PIPURL:
              session['u'] = globs.PIPURL
            raise SystemExit
          except gspread.exceptions.NoValidUrlKeyFound:
            try:
              gdoc = gsp.open(globs.NAME)
              globs.DOCID = gdoc.id
              if targettab:
                globs.sheet = gdoc.worksheet(targettab)
                globs.TAB = gdoc.worksheet(targettab).title
              else:
                globs.sheet = gdoc.sheet1
                globs.TAB = gdoc.sheet1.title
              stop = False
              break
            except gspread.httpsession.HTTPError, e:
              # This should redirect to a login, rather than display a message
              # but you can't redirect from inside a generator. Address later.
              out("No token found, session expired. Switch to HTML5 localStorage.")
              if globs.WEB:
                yme = 'I am sorry, the sesson has expired. Please <a href="%s">log back in.</a>' % getLoginlink()
                yield yme, "Log back in", "", ""
                yield warning
                yield flush
              raise SystemExit
            except:
              if globs.WEB:
                yield "Please <a href='https://docs.google.com/spreadsheets/create' target='_blank'>create a spreadsheet</a> named \"Pipulate\" and click button again.", "Google Spreadsheet Not Found.", "", ""
                yield warning
                yield flush
              raise StopIteration
          except gspread.exceptions.SpreadsheetNotFound:
            if globs.WEB: yield "Please give the document a name to force first save.", "", "", ""
            break
          except Exception as e:
            if globs.WEB: yield dontgetfrustrated(x)
            out("Retry login %s of %s" % (x, 10))
            time.sleep(6)
        if stop:
          if globs.WEB:
            yield badtuple
            yield spinerr
            yield unlock
          raise StopIteration
        globs.DOCLINK = '<b><a href="%s/d/%s/edit#gid=0" target="_blank">%s<i class="pip-icon pip-link-ext"></i></a></b>' % (globs.SHEETS, globs.DOCID, globs.NAME)
      out("END LOGIN ATTEMPT", "2", '-')

      if globs.WEB: yield unlock
      out("%s successfully opened." % globs.NAME)
      yme = 'Successfully opened spreadsheet: %s' % globs.DOCLINK
      yield yme, "Spreadsheet Opened", "", ""
      yield flush

      if (globs.MODE == 'keywords'
        and globs.KEYWORDS
        and globs.KEYWORDS[:1] != '['
        and globs.KEYWORDS[-1:] != ']'
        and globs.KEYWORDS[:1] != '{'
        and globs.KEYWORDS[-1:] != '}'
        ):
        # Keywords Tab
        if globs.WEB: yield "Keyword Harvesting Detected", "Making Harvest Tab if needed", "", ""
        headers = ['Keyword', 'Source']
        if globs.WEB: yield lock
        offset = 0
        newTab = False
        try:
          newTab = InitTab(gdoc, 'Harvest', headers)
        except:
          pass
        if newTab:
          offset = -1
        if globs.WEB: yield unlock
        ksheet = gdoc.worksheet("Harvest")
        kcount = ksheet.row_count + offset
        kwlist = globs.KEYWORDS.split(',')
        kwrows = []
        yme = "Harvesting %s keywords." % len(kwlist)
        if globs.WEB: yield yme, "Harvesting keywords", "", ""
        for kw in kwlist:
          kwrows.append([kw.strip(), globs.PIPURL])
        try:
          InsertRows(ksheet, kwrows, kcount)
        except:
          pass
        if globs.WEB:
          yme = "Keywords Harvested! %s" % globs.PBNJMAN
          yield yme, "Mmmmmm, more keywords.", json.dumps(kwlist), ""
          yield spinoff
        return #permissible here?
      #  _____           _             _           _       _        _                 A.K.A. the Instruction Processor
      # |_   _|   _ _ __(_)_ __   __ _( )___      | |_   _| | _____| |__   _____  __  Machine, or IPM. Pipulate() may
      #   | || | | | '__| | '_ \ / _` |// __|  _  | | | | | |/ / _ \ '_ \ / _ \ \/ /  get a pre-processing instruction
      #   | || |_| | |  | | | | | (_| | \__ \ | |_| | |_| |   <  __/ |_) | (_) >  <   which causes Pipulate to call
      #   |_| \__,_|_|  |_|_| |_|\__, | |___/  \___/ \__,_|_|\_\___|_.__/ \___/_/\_\  itself, interpret commands in tuples,
      #                          |___/                                                then come back and continue normally.

      # There's a very important point to get here, so I'll write even more. Pipulate works just fine without Turing's
      # Jukebox, but what this does is gives a chance to do other things to the spreadsheet, like add tables, setup initial
      # values, and even simulate "replace ?'s" clicks in targeted tabs BEFORE other Good Sheet starts to happen, according
      # to the conventional lawnmower-sweeping ?-replacement behavior--which you can choose to block here, or allow as the
      # final phase if you like. This is your "sheet music" reader or Turing Machine read/write head scanner.

      if preproc:
        for instruction in preproc:
          inst = instruction[0]
          if inst == 'clear':
            out('Clearing Sheet 1')
            if globs.WEB: yield "Clearing Sheet 1...", "Clearing Sheet 1", "", ""
            try:
              anything = re.compile('.+')
              CellList = gdoc.sheet1.findall(anything)
              for cell in CellList:
                cell.value = ''
              result = gdoc.sheet1.update_cells(CellList)
              if globs.WEB:
                yield "Sheet1 Cleared!", "Now, go do something awesome!", "", ""
                yield spinoff
            except:
              if globs.WEB:
                yield "Failed to clear Sheet 1", "", "", ""
                yield spinerr
              Stop()
          elif inst == 'message':
            yield instruction[1]
          elif inst == 'docs':
            yield instruction[1], '', '', ''
            yield "docs", "", "", ""
          elif inst == 'table':
            out("IPM Make table on sheet1")
            aobj = instruction[1]
            row1 = aobj[0]
            lol = aobj[1:]
            InitTab(gdoc, "sheet1", row1, lol)
          elif inst == 'sheet':
            out("IPM Make table on any sheet")
            tabname = instruction[1]
            if globs.WEB:
              yme = "Making new tab: %s" % tabname
              yield yme, "Making new tab.", "", ""
              yield flush
            aobj = instruction[2]
            row1 = aobj[0]
            lol = aobj[1:]
            tabs = [sheet.title.lower() for sheet in gdoc.worksheets()]
            if tabname in tabs:
              try:
                insertat = len(gdoc.worksheet(tabname).col_values(1))
                InsertRows(gdoc.worksheet(tabname), lol, insertat)
              except:
                pass
            else:
              InitTab(gdoc, tabname, row1, lol)
          elif inst == '?':
            if instruction[1]:
              for yieldme in Pipulate(targettab=instruction[1]):
                yield yieldme
            else:
              for yieldme in Pipulate():
                yield yieldme
          elif inst == 'fillmarks' or inst == 'resetmarks': #Fill in question marks
            if not globs.row1:
              globs.row1 = lowercaselist(gdoc.worksheet(globs.TAB).row_values(1))
            if not globs.numrows:
              globs.numrows = len(gdoc.worksheet(globs.TAB).col_values(1))
            if int(globs.numrows) > 1:
              colrange = None
              for acol in globs.row1:
                if acol in globs.funcscrapes:
                  yme = "Resetting ?'s for %s" % acol
                  if globs.WEB:
                    yield yme, "", "", ""
                    yield flush
                  qcol = globs.letter[globs.row1.index(acol) + 1]
                  nr = globs.numrows
                  colrange = '%s%s:%s%s' % (qcol, 2, qcol, nr)
                  CellList = globs.sheet.range(colrange)
                  for cell in CellList:
                    if inst == 'resetmarks':
                      cell.value = '?'
                    elif not cell.value:
                      cell.value = '?'
                  result = globs.sheet.update_cells(CellList)
              yield "Question marks filled in!", "Ready to pipulate.", "", ""
            else:
              if globs.WEB:
                yield "Sheet too short for ?'s.", "", "", ""
                yield warning
                yield flush
              raise SystemExit
          elif inst == 'add':
            if not globs.row1:
              globs.row1 = lowercaselist(gdoc.worksheet(globs.TAB).row_values(1))
            colname = instruction[1]
            if colname not in globs.row1:
              clet = globs.letter[len(gdoc.worksheet(globs.TAB).row_values(1)) + 1]
              acell = "%s1" % clet
              globs.sheet.update_acell(acell, instruction[1])
              globs.row1 = lowercaselist(globs.sheet.row_values(1))
              out(instruction)
          elif inst == 'stop':
            out("This is a forced-stop from the IPM")
            if globs.WEB:
              yme = "Pipulation Complete! Do a little victory dance!" + globs.PBNJMAN
              yield yme, "Pipulation Complete!", "", ""
              yield spinoff
              yield finished
              yield flush
            raise SystemExit
      #                        _       _               _  ___   At some point in the future, there wil be
      #   __ _  ___   ___   __| |  ___| |__   ___  ___| ||__ \  something better than Google Spreadsheets.
      #  / _` |/ _ \ / _ \ / _` | / __| '_ \ / _ \/ _ \ __|/ /  Until that day, let us use it excessively
      # | (_| | (_) | (_) | (_| | \__ \ | | |  __/  __/ |_|_|   for precisely the things it's good at. But
      #  \__, |\___/ \___/ \__,_| |___/_| |_|\___|\___|\__(_)   it must be there, you must have access, any
      #  |___/                                                  servers in the picture must have access too.

      # Documentation Tab
      if 'docs' in gdoc.worksheets():
        if len(documentation()) > gdoc.worksheet("Docs").row_count:
          if globs.WEB:
            yield "Re-creating the Docs tab (new functions added).", "New Function Added", "", ""
          out("Re-creating Docs Tab")
          try:
            gdoc.del_worksheet(gdoc.worksheet("Docs"))
          except:
            pass
        #gotcha((gdoc.worksheet("Docs").row_count, len(documentation())))
      headers = ['Function', 'Category', 'Requirements', 'Description', 'More']
      InitTab(gdoc, 'Docs', headers, documentation()) #!!!

      # Config Tab
      headers = ['NAME', 'VALUE']
      config = []
      config.append(['RepeatJobEvery','day'])
      config.append(['MaxRowsPerHour',''])
      config.append(['SEMRush','Paste SEMRush API key here.'])
      config.append(['MozID','Paste Moz ID here.'])
      config.append(['MozKey','Paste Moz Secret Key here.'])
      if globs.WEB: yield lock
      try:
        InitTab(gdoc, 'Config', headers, config)
      except:
        Stop()
      if globs.WEB: yield unlock

      # Scrapers Tab
      headers = ['name', 'type', 'pattern']
      InitTab(gdoc, 'Scrapers', headers, scrapes())
      sst = None
      out("Loading Scrapers.")
      stop = True
      for x in range(5):
        if globs.WEB: yield lock
        try:
          sst = gdoc.worksheet("Scrapers")
          stop = False
          break
        except:
          if globs.WEB: yield dontgetfrustrated(x)
          out("Retry get Scraper sheet %s of %s" % (x, 5))
          time.sleep(3)
      if stop:
        if globs.WEB:
          yield badtuple
          yield spinerr
          yield unlock
        raise StopIteration
      tabs = None
      try:
        tabs = [sheet.title for sheet in gdoc.worksheets()]
      except:
        pass
      if tabs:
        out("Tabs Read!")
        if globs.WEB:
          yield "Required tabs for Pipulate successfully found/created!", "Tabs created", tabs, ""
          yield flush
      #        _       _                           __ _
      #   __ _| | ___ | |__  ___   ___ ___  _ __  / _(_) __ _
      #  / _` | |/ _ \| '_ \/ __| / __/ _ \| '_ \| |_| |/ _` |
      # | (_| | | (_) | |_) \__ \| (_| (_) | | | |  _| | (_| |
      #  \__, |_|\___/|_.__/|___(_)___\___/|_| |_|_| |_|\__, |
      #  |___/                                          |___/
      stop = True
      for x in range(5):
        if globs.WEB: yield lock
        try:
          out("Reading Config tab into globals.")
          globs.config = RefreshConfig(gdoc, "Config") #HTTPError
          stop = False
          break
        except:
          if globs.WEB: yield dontgetfrustrated(x)
          out("Retry Reading Config tab into globals %s of %s" % (x, 10))
          time.sleep(5)
      if stop:
        if globs.WEB:
          yield badtuple
          yield spinerr
          yield unlock
        raise StopIteration
      out("Config tab copied to globals.")

      if not globs.tabnames:
        globs.worksheets = gdoc.worksheets()
        globs.tabnames = [sheet.title for sheet in globs.worksheets]

      # The ideal place to check if one of the table names appears in the config tab names
      for item in globs.tabnames:
        for name in globs.config:
          if name.lower() == item.lower():
            if globs.config[name] == 'list':
              globs.obs[name] = gdoc.worksheet(item).get_all_values()

      # I should apply this to everything that can get "bumped up" to globs from globs.config
      if 'maxrows' in globs.config:
        try:
          globs.maxrows = int(globs.config['maxrows'])
        except:
          pass

      maxrowsperhour = 0
      if 'maxrowsperhour' in globs.config:
        maxrowsperhour = globs.config['maxrowsperhour']
      out("maxrowsperhour: %s" % maxrowsperhour)
      secondsbetweenrows = 0
      if 'secondsbetweenrows' in globs.config and globs.config['secondsbetweenrows']:
        secondsbetweenrows = int(globs.config['secondsbetweenrows'])
      out("secondsbetweenrows : %s" % secondsbetweenrows)
      out("Counting rows in Pipulate tab.")
      stop = True
      for x in range(5):
        if globs.WEB: yield lock
        try:
          if targettab:
            globs.sheet = gdoc.worksheet(targettab)
          else:
            globs.sheet = gdoc.sheet1
          stop = False
          break
        except:
          if globs.WEB: yield dontgetfrustrated(x)
          out("Retry get Pipulate sheet %s of %s" % (x, 10))
          time.sleep(5)
      if stop:
        if globs.WEB:
          yield badtuple
          yield spinerr
          yield unlock
        raise StopIteration
      stop = True
      for x in range(5):
        if globs.WEB: yield lock
        try:
          CellList = globs.sheet.findall("?")
          for cell in CellList:
            qset.add(cell.row)
          stop = False
          break
        except:
          if globs.WEB: yield dontgetfrustrated(x)
          out("Retry get rows with question marks %s of %s" % (x, 10))
          time.sleep(5)
      if stop:
        if globs.WEB:
          yield badtuple
          yield spinerr
          yield unlock
        raise StopIteration
      stop = True
      for x in range(10):
        if globs.WEB: yield lock
        try:
          globs.numrows = len(globs.sheet.col_values(1)) #!!!UnboundLocalError HTTPError OPTIMIZE!
          stop = False
          break
        except:
          if globs.WEB: yield dontgetfrustrated(x)
          out("Retry count rows %s of %s" % (x, 10))
          time.sleep(10)
      if stop == True:
        if globs.WEB:
          yield spinerr
          yield unlock
        Stop()
      if globs.numrows == 0:
        if globs.WEB:
          yield "Nothing to pipulate.", "Make sure sheet is set up correctly.", "", ""
          yield warning
          yield unlock
          yield flush
        raise SystemExit
      elif globs.numrows > globs.maxrows:
        yme = "%s rows is too many rows. Max is %s." % (globs.numrows, globs.maxrows)
        if globs.WEB:
          yield yme, "Too many rows for Pipulate", "", ""
          yield "Use this link to run job in background.", "", "", ""
          yield "You will be able to stop the job from the Config tab.", "", "", ""
          yield spinerr
          yield unlock
        yield stopit
      s = ''
      if globs.numrows > 1:
        s = 's'
      yme = "%s row%s found in %s." % (globs.numrows, s, globs.TAB)
      out(yme)
      if globs.WEB:
        yield yme, "", "", ""
        yield flush
      if globs.numrows == 0 and globs.MODE == 'qmarks':
        if globs.WEB:
          yme = "Ready to go, but no question marks found."
          yield yme, "Pipulate needs question marks to replace.", "", ""
          yield spinerr
        return #permissible here?

      stop = True
      for x in range(5):
        try:
          lod = sst.get_all_records() #Returns list of dictionaries
          stop = False
          break
        except:
          if globs.WEB: yield dontgetfrustrated(x)
          out("Retry count rows %s of %s" % (x, 10))
          time.sleep(10)
      if stop == True:
        if globs.WEB:
          yield badtuple
          yield spinerr
          yield unlock
        raise StopIteration
      pat = [[d['pattern']][0] for d in lod]
      typ = [[d['type']][0] for d in lod]
      nam = [[d['name']][0] for d in lod]
      scrapetypes = ziplckey(nam, typ)
      scrapepatterns = ziplckey(nam, pat)
      transscrape = ziplckey(nam, nam)
      out("Scrapers loaded.")
      out("Loading row1 into globals.")
      stop = True
      for x in range(10):
        if globs.WEB: yield lock
        try:
          globs.row1 = lowercaselist(globs.sheet.row_values(1))
          stop = False
          break
        except:
          if globs.WEB: yield dontgetfrustrated(x)
          out("Retry load Row1 %s of %s" % (x, 10))
          time.sleep(5)
      if stop:
        if globs.WEB:
          yield badtuple
          yield spinerr
          yield unlock
        raise StopIteration
      trendlistoflists = []
      out("Scanning row 1 for function and scraper names.")
      fargs = {}
      for coldex2, fname in enumerate(globs.row1):
        try:
          fname = fname.lower()
        except:
          pass
        if fname in transfuncs.keys():
          out("Found function %s in row 1." % fname)
          fargs[coldex2] = {}
          from inspect import getargspec
          #  _____       _ _   _____            _     _  _   _  Evil Eval #1
          # | ____|_   _(_) | | ____|_   ____ _| |  _| || |_/ |
          # |  _| \ \ / / | | |  _| \ \ / / _` | | |_  ..  _| | Turns string-name of a function into an actual
          # | |___ \ V /| | | | |___ \ V / (_| | | |_      _| | instance of that function. Can only do this if
          # |_____| \_/ |_|_| |_____| \_/ \__,_|_|   |_||_| |_| it was already found to exist in globals.
          #
          argspec = getargspec(eval(fname))
          if argspec:
            out("%s has arguments." % (fname))
            myargs = argspec[0]
            mydefs = argspec[3]
            offset = 0
            if mydefs:
              out("%s has defaults," % (fname))
              offset = len(myargs) - len(mydefs)
              if offset:
                for i in range(0, offset-1):
                  fargs[coldex2][myargs[i]] = None
                for i in range(offset, len(myargs)):
                  fargs[coldex2][myargs[i]] = mydefs[offset-i]
            else:
              out("%s has no defaults." % (fname))
              for anarg in myargs:
                fargs[coldex2][anarg] = None
            for argdex, anarg in enumerate(myargs): #For each argument of function
              fargs[coldex2][anarg] = None
      #            _            _     _
      #   __ _ ___| |_ ___ _ __(_)___| | _____
      #  / _` / __| __/ _ \ '__| / __| |/ / __|
      # | (_| \__ \ ||  __/ |  | \__ \   <\__ \
      #  \__,_|___/\__\___|_|  |_|___/_|\_\___/
      #
      trended = False
      out("Scan down Pipulate tab looking for ASTERISKS.", "2")

      for rowdex in range(1, globs.numrows+1):
        out("Scanning row %s for asterisks." % rowdex) #This can have a pretty long delay

        stop = True
        for x in range(8):
          if globs.WEB: yield lock
          try:
            onerow = globs.sheet.row_values(rowdex) #!!! HTTPError OPTIMIZE THIS!
            stop = False
            break
          except:
            if globs.WEB: yield dontgetfrustrated(x)
            out("Retry %s of %s" % (x, 8))
            time.sleep(5)
        if stop:
          if globs.WEB:
            yield badtuple
            yield spinerr
            yield unlock
          raise StopIteration
        if onerow:
          if rowdex == 2: #Looking for trending requests
            if '*' in onerow:
              trended = True
              out("Found asterisks on row 2 -- trending activated!")
              trendlistoflists.append(onerow)
              if globs.WEB: yield "Found asterisks indicating trending in row 2", "Then we look for trending job requests...", json.dumps(onerow), ""
            else:
              break
          elif trendlistoflists and rowdex > 2:
            if '*' in onerow:
              out("Found astrisks on row %s." % rowdex)
              trendlistoflists.append(onerow)
              yme = ", %s" % rowdex
              if globs.WEB: yield yme, "", json.dumps(onerow), ""
            else:
              blankrows += 1
              if blankrows > 1:
                out("Found second row without asterisks, so stopped looking.")
                break
        else:
          blankrows += 1
          if blankrows > 1:
            out("Found second blank row, so trending scan complete.")
            break
      if len(trendlistoflists) > 0:
        yme = "%s trending jobs found. Analyzing frequency." % len(trendlistoflists)
        if globs.WEB: yield yme, "", "", ""
      trendingrowsfinished = True
      out("Done looking for asterisks", "2", "-")
      #  _   _                   ___                           _
      # | |_(_)_ __ ___   ___   ( _ )     ___ ___  _   _ _ __ | |_
      # | __| | '_ ` _ \ / _ \  / _ \/\  / __/ _ \| | | | '_ \| __|
      # | |_| | | | | | |  __/ | (_>  < | (_| (_) | |_| | | | | |_
      #  \__|_|_| |_| |_|\___|  \___/\/  \___\___/ \__,_|_| |_|\__|
      #
      out("Count and timestamp columns for TRENDING", '2')
      times = []
      if trended and 'count' in globs.row1:
        backintime = globs.numrows - len(trendlistoflists) + 1
        countletter = globs.letter[globs.row1.index('count') + 1]
        mayhaverun = "%s%s:%s%s" % (countletter, backintime, countletter, globs.numrows)
        try:
          CellList = globs.sheet.range(mayhaverun)
        except:
          out("Failed to load the trending Count range.")
          Stop()
        counts = []
        for onecell in CellList:
          counts.append(onecell.value)
        samecount = all(x == counts[0] for x in counts)
        if samecount:
          if counts[0] == '*':
            counts[0] = 0
          #Here we need to detect if there's rows left over.
          try:
            timeletter = globs.letter[globs.row1.index('timestamp') + 1]
          except:
            Stop()
          mayhaverun = "%s%s:%s%s" % (timeletter, backintime, timeletter, globs.numrows)
          try:
            CellList = globs.sheet.range(mayhaverun)
          except:
            out("Failed to load the trending timestamp range.")
          for onecell in CellList:
            times.append(onecell.value)
          trendingrowsfinished = times.count('?') == 0
          if trendingrowsfinished:
            maxrowsperhour = len(trendlistoflists)
            if not counts[0]:
              if globs.WEB: yield "Last set of trending rows complete.", "", "", ""
          try:
            int(maxrowsperhour)
          except:
            maxrowsperhour = 0
          if not trendingrowsfinished:
            qstart = globs.numrows - times.count('?') + 1
            trendlistoflists = []
          nextnum = int(counts[0]) + 1
          for onelist in trendlistoflists:
            onelist[globs.row1.index('count')] = nextnum

      if trended and trendingrowsfinished == True:
        qstart = globs.numrows + 1
        qend = globs.numrows + 1
        qset.add(globs.numrows + 1)
      elif qset:
        qstart = min(qset)
        qend = max(qset) + 1
      else:
        qstart = 1
        qend = globs.numrows + 1
      out("Done count and timestamp columns for trending", '2', '-')
      #  _                     _
      # (_)_ __  ___  ___ _ __| |_   _ __ _____      _____
      # | | '_ \/ __|/ _ \ '__| __| | '__/ _ \ \ /\ / / __|
      # | | | | \__ \  __/ |  | |_  | | | (_) \ V  V /\__ \
      # |_|_| |_|___/\___|_|   \__| |_|  \___/ \_/\_/ |___/
      #
      out("INSERT NEW ROWS for new time increment trending", '2')
      #jobstats = timewindow(times[0])
      if times:
        insert, name, number, left, right, now = timewindow(times[0])
      else:
        insert, name, number, left, right, now = False, False, False, False, False, False
      if name and number:
        tellrow = maxrowsperhour
        if tellrow == 0:
          tellrow = 'all'
        if globs.WEB: yield "Job requested to process %s row(s) every %s %s" % (tellrow, number, name), "", "", ""
      if left and right and now:
        if globs.WEB:
          yield "%s = Start of last time window" % left, "", "", ""
          yield "%s = End of last time window" % right, "", "", ""
          yield "%s = Currrent time" % now, "", "", ""
      if trendlistoflists and insert: #This line will show in errors for any Config scheduling screw-ups.
        for x in range(4):
          try:
            InsertRows(globs.sheet, trendlistoflists)
          except:
            if globs.WEB: yield dontgetfrustrated(x)
            out("Error on trending, retry %s" % x)
            time.sleep(2)
          else:
            trendlistoflists = []
            break
      #We need to get it again if trending rows were added. !!! Optimize
      if trended:
        try:
          if targettab:
            globs.sheet = gdoc.worksheet(targettab)
          else:
            globs.sheet = gdoc.sheet1
        except:
          if globs.WEB:
            yield "Couldn't reach Google Docs. Try logging in again.", "", "", ""
            yield spinoff
          Stop()
        else:
          pass
      globs.numrows = len(globs.sheet.col_values(1))
      if trended:
        qend = globs.numrows + 1
      #globs.numrows = globs.numrows + len(trendlistoflists) #faster
      out("Done insert new rows for new time inrement trending", '2', '-')
      #                        _   _                                    _
      #   __ _ _   _  ___  ___| |_(_) ___  _ __    _ __ ___   __ _ _ __| | _____
      #  / _` | | | |/ _ \/ __| __| |/ _ \| '_ \  | '_ ` _ \ / _` | '__| |/ / __|
      # | (_| | |_| |  __/\__ \ |_| | (_) | | | | | | | | | | (_| | |  |   <\__ \
      #  \__, |\__,_|\___||___/\__|_|\___/|_| |_| |_| |_| |_|\__,_|_|  |_|\_\___/
      #     |_|
      out("QUESTION MARK Replacement.", '2')
      if not qset and not trended:
        # Yield values that will un-nest console output
        if globs.WEB:
          yme = "No ?'s found in sheet."
          yield yme, "The first worksheet in your spreadsheet needs to be set up.", "", ""
          yield warning
          yield flush
          yield finished
          yield flush
        yield stopit
      if not [i for i in globs.row1 if i in globs.funcscrapes]:
        if globs.WEB:
          yme = "No Pipulate functions found in %s tab." % globs.TAB
          yield yme, "Look at the list of options under the Docs tab.", "", ""
          yield warning
          yield finished
          yield flush
        yield stopit
      therange = range(qstart, qend)
      blankrows = 0 #Lets us skip occasional blank rows
      for index, rowdex in enumerate(therange): #Start stepping through every row.
        if rowdex in qset:
          out("maxrowsperhour: %s" % maxrowsperhour)
          out("index: %s" % index)
          if maxrowsperhour and index >= int(maxrowsperhour):
            if globs.WEB:
              yme = "Maximum number of rows (%s) reached on this run." % maxrowsperhour
              yield yme, "Maximum rows-per-click processed", "", ""
            break
          if secondsbetweenrows:
            out("Waiting %s seconds between rows..." % secondsbetweenrows)
            if globs.WEB:
              yme = "Waiting %s seconds between processing each row." % secondsbetweenrows
              yield yme, "", "", ""
            time.sleep(secondsbetweenrows)
          yme = "Pipulating row: %s (item %s of %s)..." % (rowdex-1, index+1, len(therange))
          yield yme, yme, "", ""
          globs.hobj = None
          globs.html = '' #Blank the global html object. Recylces fetches.
          rowrange = "A%s:%s%s" % (rowdex, globs.letter[len(globs.row1)], rowdex)

          stop = True
          for x in range(5):
            if globs.WEB: yield lock
            try:
              CellList = globs.sheet.range(rowrange)
              stop = False
            except:
              out("Retry %s of %s" % (x, 5))
              time.sleep(2)
              if globs.WEB: yield dontgetfrustrated(x)
          if stop:
            if globs.WEB:
              yield "GData Timed Out","Sorry, GDATA Failed. Try again.", "", ""
              yield spinerr
              yield unlock
            yield stopit

          onerow = []
          for cell in CellList:
            onerow.append(cell.value)
          if '?' in onerow:
            #   _ __ _____      __  Inside the Monolithic Generator, there resides a very special location where you are
            #  | '__/ _ \ \ /\ / /  about to step through rows and actually replace any that contain a question mark.
            #  | | | (_) \ V  V /   What's so special about this place? Well, user feedback, of course! Anything you want
            #  |_|  \___/ \_/\_/    to show to the user once-per-row must yield it's output from the generator here.
            #
            out("PROCESSING ROW %s." % rowdex, '3')
            blankrows = 0
            if globs.WEB:
              yield "", "", json.dumps(onerow), ""
            rowdexstring = str(rowdex)
            newrow = onerow[:]
            if rowdexstring > 1:
              #All subsequent rows are checked for question mark replacement requests.
              for coldex, acell in enumerate(newrow):
                if questionmark(onerow, rowdexstring, coldex):
                  if 'url' in globs.row1: #Only fetch html once per row if possible
                    if globs.WEB: yield lock
                    try:
                      # if 'archive' in globs.row1:
                      #   prehtml = onerow[globs.row1.index('archive')]
                      #   gotcha("2")
                      #   globs.html = unarchive(prehtml)
                      # else:
                      #   globs.html = gethtml(onerow[globs.row1.index('url')])
                      globs.html = gethtml(onerow[globs.row1.index('url')])
                    except:
                      pass
                    if globs.WEB: yield unlock
                  collabel = globs.row1[coldex]
                  if collabel in transfuncs.keys():
                    stop = True
                    retries = 3
                    delay = 5
                    for x in range(1, retries+1):
                      #   __                  _   _
                      #  / _|_   _ _ __   ___| |_(_) ___  _ __  ___
                      # | |_| | | | '_ \ / __| __| |/ _ \| '_ \/ __|
                      # |  _| |_| | | | | (__| |_| | (_) | | | \__ \
                      # |_|  \__,_|_| |_|\___|\__|_|\___/|_| |_|___/
                      #
                      out("Function Start", "4")
                      fname = transfuncs[globs.row1[coldex]]
                      farg = fargs[coldex]
                      evalme = "%s(" % fname #Begin building string that will eventually be eval'd
                      yme = "<li>%s...</li>" % (collabel)
                      if globs.WEB:
                        yield yme, "", "", ""
                        yield flush
                      if farg:
                        #The function we're looking at DOES have required arguments.
                        for anarg in farg:
                          #Add an arg=value to string for each required argument.
                          anarg = anarg.lower()
                          argval = getargval(anarg, farg[anarg], newrow)
                          evalme = "%s%s=%s, " % (evalme, anarg, argval)
                        evalme = evalme[:-2] + ')' #Finish building string for the eval statement.
                      else:
                        #No arguments required, so just immediately close the parenthesis.
                        evalme = evalme + ')'
                      try:
                        #  _____       _ _   _____            _     _  _  ____    Evil Eval #2
                        # | ____|_   _(_) | | ____|_   ____ _| |  _| || ||___ \
                        # |  _| \ \ / / | | |  _| \ \ / / _` | | |_  ..  _|__) |  Turns a function-call string signature
                        # | |___ \ V /| | | | |___ \ V / (_| | | |_      _/ __/   into an actual instance of that function
                        # |_____| \_/ |_|_| |_____| \_/ \__,_|_|   |_||_||_____|  called with those parameters. Grok it.
                        #
                        try:
                          tastereturn = eval(evalme)
                        except Exception as e:
                          errortype, errormessage, traceback = sys.exc_info()
                          errortype = errortype.__name__
                          fname = os.path.split(traceback.tb_frame.f_code.co_filename)[1]
                          lineno = traceback.tb_lineno
                          out("errortype: %s" % errortype)
                          out("errormessage: %s" % errormessage)
                          out("traceback: %s" % traceback)
                          out("Exception: %s" % Exception)
                          yield "Problem in function", "", "", ""
                          Stop() #                                            <-- This is where you could keep things running
                        if type(tastereturn) == tuple:
                          newrow[coldex] = tastereturn[0]
                          if len(tastereturn) > 1:
                            checkdict = tastereturn[1]
                            if type(checkdict) == dict:
                              for index2, anothercell in enumerate(CellList):
                                #out("'%s': '%s'" % (globs.row1[index2], anothercell.value))
                                for akey in checkdict:
                                  #out("'%s': '%s'" % (akey, checkdict[akey]))
                                  if globs.row1[index2] == akey:
                                    anothercell.value = checkdict[akey]
                                    newrow[index2] = checkdict[akey]
                              #result = globs.sheet.update_cells(CellList)
                              #break
                        else:
                          newrow[coldex] = tastereturn
                        stop = False
                        out('%s worked' % collabel)
                        break
                      except Exception as e:
                        errortype, errormessage, traceback = sys.exc_info()
                        errortype = errortype.__name__
                        fname = os.path.split(traceback.tb_frame.f_code.co_filename)[1]
                        lineno = traceback.tb_lineno
                        out("errortype: %s" % errortype)
                        out("errormessage: %s" % errormessage)
                        out("traceback: %s" % traceback)
                        out("Exception: %s" % Exception)
                        if globs.WEB:
                          yield e, e, '', ''
                          yield warning
                          yme = "%s in function: %s in file %s line %s." % (errortype, collabel, fname, lineno)
                          yield yme, yme, '', ''
                          yield spinerr
                          yield flush
                        # !!!
                        #yield stopit
                        #raise SystemExit
                        
                        #if globs.WEB:
                        #  yme = 'Problem in %s. Retry #%s of %s in <span class="countdown">%s</span> seconds...' % (collabel, x, retries, delay*x)
                        #  yme2 = 'Problem in %s. Retry #%s of %s...' % (collabel, x, retries)
                        #  yield yme, yme2, "", ""
                        #  yield "countdown", "", "", ""
                        #  yield warning
                        #time.sleep(delay*x)
                    if stop == True:
                      out("Function End (Failed)", "4", '-')
                      if globs.WEB:
                        yme = "Something wrong in %s. ?-Replacement did not complete." % collabel
                        yield yme, "", "", ""
                        yield spinerr
                        yield unlock
                      Stop() #                                            <-- This is where you could keep things running
                    out("Function End", "4", '-')
                  elif collabel in transscrape.keys():
                    stop = True
                    for x in range(3):
                      #  ____
                      # / ___|  ___ _ __ __ _ _ __   ___ _ __
                      # \___ \ / __| '__/ _` | '_ \ / _ \ '__|
                      #  ___) | (__| | | (_| | |_) |  __/ |
                      # |____/ \___|_|  \__,_| .__/ \___|_|
                      #                      |_|
                      out("Scrape Start", "4")
                      try:
                        out("Entering generic scraper.")
                        sname = transscrape[globs.row1[coldex]]
                        stype = scrapetypes[sname]
                        spattern = scrapepatterns[sname]
                        yme = "<li>%s...</li>" % (collabel)
                        if globs.WEB:
                          yield yme, "", "", ""
                          yield flush
                        if 'url' in globs.row1 or 'archive' in globs.row1:
                          if globs.WEB: yield lock
                          if 'archive' in globs.row1:
                            prehtml = onerow[globs.row1.index('archive')]
                            html = unarchive(prehtml)
                            if not html:
                              url = onerow[globs.row1.index('url')]
                              html = gethtml(url)
                          else:
                            url = onerow[globs.row1.index('url')]
                            html = gethtml(url)
                          if not html:
                            if globs.WEB:
                              yield "HTML not available. Possible Content-Type error. Continuing.", "Skipping this row and trying next row.", "", ""
                              yield warning
                              yield flush
                            out("HTML NOT AVAILABLE")
                            newrow[coldex] = None
                            stop = False
                            break
                          if globs.WEB: yield unlock
                          #add another elif condition for PyQuery https://pypi.python.org/pypi/pyquery
                          if stype.lower() == 'xpath':
                            import lxml.html
                            searchme = lxml.html.fromstring(html)
                            try:
                              match = searchme.xpath(spattern)
                            except lxml.etree.XPathEvalError:
                              out("BAD XPATH PATTERN")
                              yme = "Bad xpath: %s" % spattern
                              if globs.WEB:
                                yield yme, "Bad XPATH Pattern!", "", ""
                                yield spinerr
                                yield flush
                              raise SystemExit
                            except:
                              out("OTHER LXML ERROR")
                              if globs.WEB: yield "LXML parser problem. Check URL source", "LXML Problem!", "", ""
                              Stop()
                            if match:
                              if len(match) == 1:
                                newrow[coldex] = match[0]
                              else:
                                frag = ''
                                for item in match:
                                  if item.__class__.__name__ in ('HtmlElement', 'HtmlComment'):
                                    frag += stringify_children(item)
                                  else:
                                    try:
                                      frag += item
                                    except:
                                      pass
                                  frag += '\r\n'
                                newrow[coldex] = frag
                            else:
                              newrow[coldex] = None
                          elif stype.lower() == 'regex':
                            match = re.search(spattern, html, re.S | re.I)
                            if match:
                              if "scrape" in match.groupdict().keys():
                                newrow[coldex] = match.group("scrape").strip()
                              else:
                                newrow[coldex] = None
                            else:
                              newrow[coldex] = None
                        out('%s worked.' % collabel)
                        stop = False
                        break
                      except Exception as e:
                        print traceback.format_exc()
                        out("Scrape problem on row %s. Retrying." % rowdexstring)
                        time.sleep(2)
                        if globs.WEB: yield dontgetfrustrated(x)
                    if stop == True:
                      out("Scrape End (Failed)", "4", '-')
                      if globs.WEB:
                        yme = "Something went wrong in the %s scraper. Stopping." % collabel
                        yield yme, "", "", ""
                        yield spinerr
                        yield unlock
                      Stop() #                                            <-- This is where you could keep things running
                    out("Scrape End", "4", '-')
            out("DONE PROCESSING ROW %s." % rowdex, '3', '-')
            out("Finished processing row. Updating spreadsheet...")
            newrow = [globs.EMPTY if x==None else x for x in newrow]
            if len(str(newrow)) > globs.ROWMAX:
              yme = "['JSON data for %s too big to display here.']" % collabel
              if globs.WEB: yield "", "", yme, ""
            else:
              try:
                if globs.WEB: yield "", "", json.dumps(newrow), ""
              except:
                if globs.WEB: yield "", "", newrow, ""
            for index, onecell in enumerate(CellList):
              onecell.value = newrow[index]
            result = None
            stop = True
            for x in range(10):
              if globs.WEB: yield lock
              try:
                result = globs.sheet.update_cells(CellList)
                stop = False
                break
              except:
                out("Writing row to spreadsheet, retry %s of %s" %(x, 10))
                time.sleep(5)
                if globs.WEB: yield dontgetfrustrated(x)
            if stop:
              if globs.WEB:
                yield badtuple
                yield spinerr
                yield unlock
              raise StopIteration
          elif onerow.count('') == len(onerow):
            blankrows += 1
            if blankrows > 1:
              break
      out("Done question Mark Replacement.", '2', '-')
    else: #No session object found
      if globs.WEB: yield 'Please Login to Google', "", "", ""
    if globs.WEB:
      yield '<span class="newrow">?-Replacement complete.</span>', "Question marks replaced!", "", ""
      yield success
      yield flush
      yield spinoff
    yield stopit
    out("PIPULATION OVER", "1", '-')
  except Exception as e:
    exceptiondata = traceback.format_exc()
    print(exceptiondata)
    exceptionlines = exceptiondata.splitlines()
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    ename = type(e).__name__
    fixme = "Error: %s, File: %s, Line: %s" % (ename, fname, exc_tb.tb_lineno)
    out(fixme)
    out("Pipulation Failure")
    if ename == "StopIteration":
      loginmsg = ""
      if session and 'loggedin' in session and session['loggedin'] != '1':
        loginmsg = "Login link under the upper-left \"burger button\"."
      # if globs.WEB: yield "Session timed out. Try again", "If at first you don't succeed, pipulate again.", "", ""
    else:
      if globs.WEB:
        yield exceptionlines[-1], "", "", ""
        yield fixme, "", "", ""
        yield "Pipulation prematurely terminated.", "", "", ""
        yield "Please open an issue at https://github.com/miklevin/pipulate", "", "", ""
        yield "Or just tap me on the shoulder.", "", "", ""
        if globs.MODE != 'clear':
          yield spinerr
    out("PIPULATION ERROR", "1", '-')
  out("EXITING MAIN", "0", '-') #Special case of function exit reporting
  print("\n")

def url_root(url):
  """Return root domain from url"""
  parsed = urlparse.urlparse(url)
  return "%s://%s%s" % (parsed[0], parsed[1], parsed[2])

def firstdir(url):
  """Return path from url"""
  parsed = urlparse.urlparse(url)
  path = parsed[2]
  pathlist = path.split("/")
  fpath = pathlist[1]
  if '.' not in fpath:
    return fpath
  else:
    return ""

def getLoginlink(gobackurl=''):
  """Return the HTML code required for an OAuth2 login link."""
  redir = globs.DOMURL
  if gobackurl:
    redir = gobackurl
  if 'Host' in request.headers:
    redir = 'http://'+request.headers['Host']
  try:
    if session and request.args and 'u' in request.args:
      session['u'] = request.args.get('u')
  except:
    pass
  scope = 'https://spreadsheets.google.com/feeds/'
  if globs.PCOM:
    scope = 'profile email ' + scope
  baseurl = globs.OAUTHURL
  cid = ''
  cid = app.config['CLIENT_ID']
  qsdict = {  'scope': scope,
              'response_type': 'token',
              'redirect_uri': redir,
              'client_id': cid
            }
  from urllib import urlencode
  return "%s?%s" % (baseurl, urlencode(qsdict))

def getLabel():
  url = request.base_url
  parsed = urlparse.urlparse(url)
  subdomain = parsed.hostname.split('.')[0]
  blab = globs.NAME
  droidcut = "ppp"
  if subdomain == 'localhost':
    blab = "%s %s 8888" % (droidcut, "Localhost")
  elif subdomain == 'pipulate':
    blab = '%s %s' % (droidcut, "Pipulate")
  elif subdomain:
    blab = "%s %s (%s)" % (droidcut, "Pipulate", subdomain)
  return blab

def getBookmarklet():
  """Return the HTML required to create a draggable Pipulate bookmarklet link."""
  host = request.headers['Host']
  bname = globs.NAME
  #return '''javascript:(function(){window.open('http://%s/?u='+encodeURIComponent(document.location.href)+'&d='+Date.now()+'&s='+encodeURIComponent(window.getSelection?window.getSelection():document.selection.createRange().text)+'&c='+window.btoa(unescape(encodeURIComponent(document.cookie))), '%s', 'toolbar=0,resizable=1,scrollbars=1,status=1,width=630,height=600');})();''' % (host, bname)
  return '''javascript:(function(){open('http://%s/?u='+encodeURIComponent(document.location.href)+'&d='+Date.now()+'&s='+encodeURIComponent(window.getSelection?window.getSelection():document.selection.createRange().text)+'&c='+window.btoa(unescape(encodeURIComponent(document.cookie))));})();''' % (host)

def getLogoutlink():
  """Return the HTML required to clear and expire the current OAuth2 token."""
  from urllib import quote_plus
  u = ''
  host = request.headers['Host']
  if session and 'u' in session:
    u = session['u']
  elif request.args and 'u' in request.args:
    u = request.args.get('u')
  if u:
    u = quote_plus(u)
  if u:
    logout = "http://%s?logout&u=%s" % (host, u)
  else:
    logout = "http://%s?logout" % host
  return logout

def RefreshConfig(gdoc, sheetname):
  #!!! Needs optimization

  stop = True
  for x in range(5):
    try:
      onesheet = gdoc.worksheet(sheetname)
      stop = False
      break
    except:
      out("Retry %s of %s" %(x, 5))
      time.sleep(2)
  if stop:
    Stop()

  stop = True
  for x in range(5):
    try:
      names = onesheet.col_values(1)
      stop = False
      break
    except:
      out("Retry %s of %s" %(x, 5))
      time.sleep(2)
  if stop:
    Stop()

  stop = True
  for x in range(5):
    try:
      values = onesheet.col_values(2)
      stop = False
      break
    except:
      out("Retry %s of %s" %(x, 5))
      time.sleep(2)
  if stop:
    Stop()

  return ziplckey(names, values)

def ziplckey(keys, values):
  keys = lowercaselist(keys)
  return dict(zip(keys, values))

def timewindow(amiinnewtimewindow):
  if amiinnewtimewindow == "*":
    return (True,'','','','','')
  intervallanguage = ""
  intervalnumber= ""
  intervalname=""
  intervalparts=[]
  if 'repeatjobevery' in globs.config:
    intervallanguage = globs.config['repeatjobevery'].strip()
    if ' ' in intervallanguage:
      intervalparts=intervallanguage.split()
      intervalname = intervalparts[1]
      if intervalname:
        intervalname = intervalname.lower()
      intervalnumber = intervalparts[0]
      out("Parsed out interval name: %s" % intervalname)
      out("Parsed out interval number: %s" % intervalnumber)
    else:
      if intervallanguage.isdigit():
        intervalname = "minute"
        intervalnumber = intervallanguage
      else:
        intervalname = intervallanguage
        intervalnumber = '1'
    ltr = intervalname[:2].lower()
    if ltr == 'mi':
      intervalname = "minute"
    elif ltr == 'ho':
      intervalname = "hour"
    elif ltr == 'da':
      intervalname = "day"
    elif ltr == 'we':
      intervalname = "week"
    elif ltr == 'mo':
      intervalname = "month"
    else:
      intervalname = "minute"
    now = datetime.datetime.now()
    now2 = now
    try:
      tick = datetime.datetime.strptime(amiinnewtimewindow, "%m/%d/%Y %H:%M:%S")
    except:
      tick = now #double-check this fall-over action
    left = None
    right = None
    try:
      intervalnumber = int(intervalnumber)
    except:
      out("Caught the type error")
      return (False,'','','','','')
    doinserts = False
    if intervalname == 'minute':
      out("Processing a %s %s interval." % (intervalnumber, intervalname))
      left = tick - datetime.timedelta(minutes=tick.minute % intervalnumber, seconds=tick.second, microseconds=tick.microsecond)
      now = now - datetime.timedelta(minutes=now.minute % intervalnumber, seconds=now.second, microseconds=now.microsecond)
      right = left + datetime.timedelta(minutes=intervalnumber)
    elif intervalname == 'hour':
      out("Processing a %s %s interval." % (intervalnumber, intervalname))
      left = tick - datetime.timedelta(hours=tick.hour % intervalnumber, minutes=tick.minute, seconds=tick.second, microseconds=tick.microsecond)
      now = now - datetime.timedelta(hours=now.hour % intervalnumber, minutes=now.minute, seconds=now.second, microseconds=now.microsecond)
      right = left + datetime.timedelta(hours=intervalnumber)
    elif intervalname == 'day':
      #Could be made shorter with use of .date()
      out("Processing a %s %s interval." % (intervalnumber, intervalname))
      left = tick - datetime.timedelta(days=tick.day % intervalnumber, hours=tick.hour, minutes=tick.minute, seconds=tick.second, microseconds=tick.microsecond)
      now = now - datetime.timedelta(days=now.day % intervalnumber, hours=now.hour, minutes=now.minute, seconds=now.second, microseconds=now.microsecond)
      right = left + datetime.timedelta(days=intervalnumber)
    elif intervalname == 'week':
      out("Processing a %s %s interval." % (intervalnumber, intervalname))
      left = find_sunday(tick.date())
      right = add_weeks(left, intervalnumber)
      now = now.date()
    elif intervalname == 'month':
      out("Processing a %s %s interval." % (intervalnumber, intervalname))
      left = tick.date().replace(day=1)
      right = left.replace(month=now.month + intervalnumber)
      now = now.date()
    else:
      out("unknown")
    out("%s last %s time interval left boundary." % (left, intervalname))
    out("%s last %s time interval right boundary." % (right, intervalname))
    out("%s is the current %s." % (now, intervalname))
    if now2 > right:
      out("We are in a new %s-boundary, so we insert rows." % intervalname)
      doinserts = True
    else:
      out("We are still within the old %s %s boundary, so skip new rows insert." % (intervalnumber, intervalname))
      doinserts = False
    rme = (doinserts, intervalname, intervalnumber, left, right, now2)
    return rme
  return (True,'','','','','')

def find_sunday(day):
  day_of_week = day.weekday()
  to_beginning_of_week = datetime.timedelta(days=day_of_week)
  beginning_of_week = day - to_beginning_of_week
  beginning_of_week = beginning_of_week - datetime.timedelta(days=1)
  return (beginning_of_week)

def add_weeks(sourcedate, weeks):
  days = weeks * 7
  daystoadd = datetime.timedelta(days=days)
  newdate = sourcedate + daystoadd
  return newdate

def InitTab(gdoc2, tabname, headerlist, listoflists=[]):
  initsheet = None
  isSheet1 = False
  for x in range(3): #not too many times here (always tried for new tabs too)
    if tabname == "sheet1":
      isSheet1 = True
      try:
        initsheet = gdoc2.sheet1
      except:
        out("Retrying connecting to Sheet 1")
        time.sleep(1)
    else:
      try:
        initsheet = gdoc2.worksheet(tabname)
        out("%s Tab exists." % tabname)
        break
      except:
        out("Retrying make %s Tab %s of %s" % (tabname, x, 3))
        time.sleep(1) #not too long here

  if isSheet1 or not initsheet:
    numcols = len(headerlist)
    if listoflists and len(listoflists) > 1 and '*' in listoflists[1]:
      numrows = len(listoflists)+1
    elif listoflists:
      numrows = len(listoflists)+2
    else:
      numrows = 2
    endletter = globs.letter[numcols]
    if isSheet1:
      newtab = gdoc2.sheet1
    else:
      newtab = gdoc2.add_worksheet(title=tabname, rows=numrows, cols=numcols)
    CellList = newtab.range('A1:%s%s' % (endletter, numrows))
    initlist = []
    for onelist in listoflists:
      for onecell in onelist:
        initlist.append(onecell)
    wholelist = list(headerlist) + list(initlist)
    for index, onecell in enumerate(CellList):
      try:
        onecell.value = wholelist[index]
      except:
        pass

    stop = True
    for x in range(5):
      try:
        newtab.update_cells(CellList)
        stop = False
        break
      except:
        out("Retry %s of %s" % (x, 5))
        time.sleep(5)
    if stop:
      Stop()
    return True
  else:
    return False

def questionmark(oldrow, rowdex, coldex):
  if rowdex != 1:
    if oldrow[coldex] == '?':
      return True
  return False

def convertisotime(timestamp):
  i = datetime.datetime(*map(int, re.split('[^\d]', timestamp)[:-1]))
  return i.strftime("%m/%d/%Y %H:%M:%S")

def getargval(anarg, defargval, onerow):
  for coldex, acol in enumerate(globs.row1):
    if acol == anarg: #Found column named same thing as a required argument.
      if onerow[coldex]: #The cell in that column has a non-zero/empty value.
        return adq(onerow[coldex]) #So, we got what we need. Return it.
  #Oops, no required arguments were found on the row.
  if defargval:
    return adq(defargval) #So, if it's got a default value, return that.
  else:
    return None #We ALWAYS have to return at least None, least errors ensue.

def adq(aval):
  if aval == None:
    return None #None-in/None-out. This special keyword shouldn't be quoted.
  else:
    return "r'''%s'''" % (aval) #ALMOST everything else should be quoted.

def stringify_children(node):
  from lxml.etree import tostring
  from itertools import chain
  parts = ([node.text] + list(chain(*([c.text, tostring(c, with_tail=False), c.tail] for c in node.getchildren()))) + [node.tail])
  # filter removes possible Nones in texts and tails
  return ''.join(filter(None, parts))
#            _    __                              _  _     _
#  __      _| |_ / _| ___  _ __ _ __ ___  ___   _| || |_  / |
#  \ \ /\ / / __| |_ / _ \| '__| '_ ` _ \/ __| |_  ..  _| | |
#   \ V  V /| |_|  _| (_) | |  | | | | | \__ \ |_      _| | |
#    \_/\_/  \__|_|  \___/|_|  |_| |_| |_|___/   |_||_|   |_|
#
from flask_wtf import Form
from wtforms import (StringField,
                    RadioField,
                    HiddenField,
                    SelectMultipleField,
                    TextAreaField,
                    SelectField,
                    widgets)

class PipForm(Form):
  """Define form for main Pipulate user interface."""
  pipurl = StringField('Paste a Google Sheet URL:')
  magicbox = TextAreaField("magicbox")
  options = SelectField("options")

class PipForm2(PipForm):
  """Adds a hidden field to tell the secondary menu from a dropdown menu selection."""
  secondary = HiddenField()

class ConfigForm(Form):
  """Define form for aquiring configuration values."""
  import binascii, os
  apdef = binascii.hexlify(os.urandom(24))
  appsecret = StringField('Flask app secret (auto-generated):', default=apdef)
  clientid = StringField('Client ID (from Google Dev Console):')
  clientsecret = StringField('Client secret (from Google Dev Console):')
#                   _
#   _ __ ___   __ _(_)_ __    _ __ ___   ___ _ __  _   _    The main menu is the dropdown menu that comes up on the main
#  | '_ ` _ \ / _` | | '_ \  | '_ ` _ \ / _ \ '_ \| | | |   Pipulate interface. It's merely a list of tuples that become
#  | | | | | | (_| | | | | | | | | | | |  __/ | | | |_| |   the select element options, and VERY MUCH setting the overall
#  |_| |_| |_|\__,_|_|_| |_| |_| |_| |_|\___|_| |_|\__,_|   tone of what it is to Pipulate. Tehnically, it is the least
#                                                           complicated of all the non-main menu stuff that follows.
def mainMenu():
  ''' Creates the entire cadence of the system.'''
  return [
    ('qmarks'      , "Replace ?'s"),
    ('repipulate'  , "Re-Pipulate"),
    ('menu:setup'  , "Do Auto Setup"),
    ('client'      , "Setup New Client"),
    ('menu:crawl'  , "Crawl a Website"),
    ('menu:column' , "Add Some Columns"),
    ('menu:graph'  , "Make Visualization"),
    ('keywords'    , "Harvest Keywords"),
    ('menu:clear'  , "Clear Sheet1")
  ]
#   ____  _           _                                                 _                    Every entry from main menu
#  |___ \( )_ __   __| | __ _ _ __ _   _   _ __ ___   ___ _ __  _   _  | | _____ _   _ ___   whose value is prefixed by
#    __) |/| '_ \ / _` |/ _` | '__| | | | | '_ ` _ \ / _ \ '_ \| | | | | |/ / _ \ | | / __|  "menu" goes as a key to pull
#   / __/  | | | | (_| | (_| | |  | |_| | | | | | | |  __/ | | | |_| | |   <  __/ |_| \__ \  up a form from the wtforms #2
#  |_____| |_| |_|\__,_|\__,_|_|   \__, | |_| |_| |_|\___|_| |_|\__,_| |_|\_\___|\__, |___/  section. The values of the
#                                  |___/                                         |___/       dict override default forms.
def secondaryMenu():
  '''Everything prefixed with "menu" in the mainMenu function becomes input here. '''
  return {
    'clear':        ClearSheet1Form(csrf_enabled=False),
    'crawl':        CrawlTypesForm(csrf_enabled=False),
    'setup':        SetupForm(csrf_enabled=False),
    'column':       AddColumnsForm(csrf_enabled=False),
    'graph':        VisualizationForm(csrf_enabled=False)
  }
#           _    __                              _  _     ____    These forms control what is in many cases, activation
# __      _| |_ / _| ___  _ __ _ __ ___  ___   _| || |_  |___ \   of tertiary actions (main menu / 2ndary menu / this).
# \ \ /\ / / __| |_ / _ \| '__| '_ ` _ \/ __| |_  ..  _|   __) |  These selections almost always result in "doing a thing"
#  \ V  V /| |_|  _| (_) | |  | | | | | \__ \ |_      _|  / __/   by pressing a jukebox "music selection" on the "IPM".
#   \_/\_/  \__|_|  \___/|_|  |_| |_| |_|___/   |_||_|   |_____|  These forms need corresponding entries in prePipulators()
#                                                                 in order to trigger the cascading player piano effect.

class SetupForm(PipForm2):
  """Create the menu for when Clear Sheet 1 is selected."""
  radios = RadioField(choices=[
    ('checklist',   'SEO Checklist'),
    ('keywordlist', 'Keyword Build'),
    ('serps',       'Setup SERP Tracking'),
    ('seocop',      'Code Cop (not ready)'),
    ('fillmarks',   "Flood-?'s (KEEPS data)."),
    ('resetmarks',  "Reset-?'s (WIPES data)."),
    ('tests',       'Run System Tests'),
    ('cancel',      'Cancel')
  ])

class AddColumnsForm(PipForm2):
  """Create the menu for when Clear Sheet 1 is selected."""
  choices = [
    ('add:URL',                                    'URL'),
    ('add:Keyword',                                'Keyword'),
    ('add:URL,Archive,Title,Description,Canonical,H1,H2,ExtractedKeyword,TopKeyword', 'Manual Crawl (title, description, canonical, h1, etc.'),
    ('add:TimeStamp,Count',                        'TimeStamp & Count (scheduling requirements)'),
    ('add:Site,Keyword,Positions,Position,TopUrl', 'SERPs (search engine results pages)'),
    ('add:Site,Keyword,LookForUrl,SERPs,Positions,TopUrl,Position,FoundUrl,InPosition', 'SERPs 2 (find particular page)'),
    ('add:RushDifficulty',                         'SEMRush Difficulty (batches 50/time)'),
    ('add:DomainAuthority,PageAuthority',          'Moz Domain and Page Authority'),
    ('add:URL,Title,Description,Canonical,H1,H2',  'Enhanced SEO Crawl fields'),
    ('add:Header,Response,Redirects',              'HTTP Header, Response Code and Redirect Chain'),
    ('add:FB,Likes,Shares,Comments',               'Facebook Likes, Shares & Comments'),
    ('add:URL,TweetTotal,Following,Followers',     'Twitter Profile (tweet total, following & followers)'),
    ('add:URL,Subscribers,Views',                  'YouTube Profile (subscribers & views)'),
    ('add:URL,Views,ThumbsUp,ThumbsDown',          'YouTube Video (views & thumbs)'),
    ('cancel',                                     'Cancel')
  ]
  checks = SelectMultipleField(
    choices=choices,
    option_widget=widgets.CheckboxInput(),
    widget=widgets.ListWidget(prefix_label=False)
  )

class CrawlTypesForm(PipForm2):
  """Present user with different types of crawls they can perform."""
  radios = RadioField(choices=[
    ('linksonpage',   '1. LINKS ON PAGE (quickest): Just get the links from page, one line per link.'),
    ('quickcrawl',    '2. LINKS OFF PAGE (quick): Same as above, but visits each page to get their on-page data.'),
    ('linkgraph',     '3. CRAWL, 2-DEEP (longer): Gathers link data required for sitemap visualization.'),
    ('pagestab',      'De-duplicate 2-DEEP crawl into new Pages tab.'),
    ('cancel',        'Cancel')
  ])

class VisualizationForm(PipForm2):
  """Offer up a few common visualizations of the type of data we're handling"""
  radios = RadioField(choices=[
    ('sitemap', 'Sitemap with 2-DEEP crawl data'),
    ('cancel',  'Cancel')
  ])

class ClearSheet1Form(PipForm2):
  """Create the menu for when Clear Sheet 1 is selected."""
  radios = RadioField(choices=[
    ('cancel',  'Cancel'),
    ('clear',   'Yes, clear Sheet 1.')
  ])

#       _               _                         _         Here's a bunch of key/value pairs for ya. We open with a
#   ___| |__   ___  ___| |_   _ __ ___  _   _ ___(_) ___    very Pythonic switch that comprise the possible instructions
#  / __| '_ \ / _ \/ _ \ __| | '_ ` _ \| | | / __| |/ __|   for our Instruction Processor Machine... or "player piano"
#  \__ \ | | |  __/  __/ |_  | | | | | | |_| \__ \ | (__    such as it were. Or Loom, if you prefer. Or Turing machine.
#  |___/_| |_|\___|\___|\__| |_| |_| |_|\__,_|___/_|\___|   In any case, we just feed these instructions into the part
#                                                           of Pipulate there waiting to execute final menu choices.

def SetupClient():
  '''Sets up new SEO client spreadsheet.'''
  out("Setting up new SEO client.")
  if not globs.PIPURL:
    if form and 'pipurl' in form:
      globs.PIPURL = form.pipurl.data
  return Pipulate([
    ('table', [
      ('url','GetLinks'),
      (globs.PIPURL, '?')
    ]),
    ('?', ''),
    ('sheet', 'Roadmap', seochecklistlist()),
    ('sheet', 'Meetings', meetings()),
    ('stop', '')
  ], label="Setting up new SEO Client...")

def KeywordChecklist():
  '''Sets up a new worksheet for the keyword build phase.'''
  out("Setting up New Keyword process.")
  return Pipulate([
    ('sheet', 'Keyword Build', keywordbuildchecklist()),
    ('sheet', 'Seeds', seedkeywordlist()),
    ('sheet', 'Expansion', expansionkeywordlist())
  ], label="Making Keyword Build tab")

def SEOChecklist():
  '''Sets up a new worksheet for tracking SEO Client setup and deliverables.'''
  out("Setting up New SEO Client.")
  return Pipulate([
    ('sheet', 'SEOChecklist', seochecklistlist()),
    ('stop', '')
  ], label='Making SEO Checklist...')

def RinseAndRepeat():
  '''Interrogates worksheet and inserts question marks wherever they can go'''
  return Pipulate([
    ('resetmarks', ''),
    ('?', ''),
    ('stop', '')
  ], label="Resetting data back to ?s and repipulating...")

def ResetQMarks():
  '''Interrogates worksheet and inserts question marks wherever they can go'''
  return Pipulate([
    ('resetmarks', ''),
    ('stop', '')
  ], label="Resetting ?'s")

def FillQMarks():
  '''Interrogates worksheet and inserts question marks wherever they can go'''
  return Pipulate([
    ('fillmarks', ''),
    ('stop', '')
  ], label="Flooding ?s")

def MakeSitemap():
  '''Offer user some visualizations to choose from.'''
  return Pipulate([
    ('sheet', 'visualizations', [
      ('viewname', 'makeview', 'sharelink', 'datestamp', 'guid', 'includecode', 'compresseddata'),
      ('sitemap', '?', '', '', '', '')
    ]),
    ('?', 'visualizations'),
    ('stop', '')
  ], label="Making Sitemap")

def AddColumns(checks):
  '''Ad columns to sheet from checkboxes on submitted form.'''
  out("Hey, I'm adding some columns!.")
  lot = []
  used = set()
  for acolumn in checks:
    if ',' in acolumn:
      subcols = [x.strip() for x in acolumn[4:].split(',')]
      for subcol in subcols:
        if subcol not in used:
          lot.append(('add', str(subcol)))
          used.add(subcol)
    else:
      if acolumn not in used:
        lot.append(('add', str(acolumn[4:])))
        used.add(acolumn[4:])
  # We return an instance of the Pipulate geneorator, fed the list-of-tuples. Nice! <-- leave this comment for awhile.
  # Pipulate is the player piano. It normally tries to replace question marks.
  # So when fed a list of tuples, it will interpret them as it's music instructions.
  lot.append(('fillmarks', ''))
  lot.append(('stop', ''))
  return Pipulate(lot, label="Adding Columns")

def RunTests():
  '''Where you're going to develop everyhing these jobs can do!.'''
  out("Running tests... Just doin' a whole bunch of stuff.")
  return Pipulate([
    ('clear', ''),
    ('sheet', 'tests', [
      ('url','Title'),
      (globs.PIPURL, '?')
    ]),
    ('?', 'tests'),
    ('stop', '')
  ], label='Run Tests')

def SERPTrack():
  '''Set up Search Engine Result Position Tracking'''
  return Pipulate([
    ('clear', ''),
    ('message', ("Setting up SERP fields.", "", "", "")),
    ('table', [
      ('Site', 'Keyword','TimeStamp', 'SERPs', 'Positions', 'Position', 'TopURL', 'Count'),
      ('[your site]', '[your keyword 1] ', '?', '?', '?', '?', '?', '1'),
      ('[your site]', '[your keyword 2]', '?', '?', '?', '?', '?', '1')
    ]),
    ('docs', 'Just set up SERPs and wondering what to do next? <a href="#">Read this doc.</a>'),
    ('stop', '')
  ], label='Setting up SERP tracking...')

def ClearSheet1():
  '''Clear Sheet 1'''
  return Pipulate([
    ('clear', ''),
    ('stop', '')
  ], label='Clearing Sheet1...')

def LinksOnPage():
  '''Collect links from displaying page.'''
  out("Getting links on page.")
  return Pipulate([
    ('clear', ''),
    ('table', [
      ('url','GetLinks'),
      (globs.PIPURL, '?')
    ])
  ], label='Getting Links On Page...')

def QuickCrawl():
  '''Collect links from displaying page and then visit each for more data..'''
  out("Getting links on page, then will visit.")
  return Pipulate([
    ('clear', ''),
    ('table', [
      ('url','GetLinks'),
      (globs.PIPURL, '?')
    ]),
    ('?', '')
  ], label='Links Off Page')

def LinkGraph():
  '''Collect links from displaying page and prepare to visit each for more links..'''
  out("Getting links on page to get links on other pages.")
  return Pipulate([
    ('clear', ''),
    ('table', [
      ('url','PreCrawl'),
      (globs.PIPURL, '?')
    ]),
    ('?', ''),
    ('stop', '')
  ], label='Crawl, 2-Deep')

def LinkGraphDeluxe():
  '''Collect links from displaying page and prepare to visit each for more links..'''
  out("Getting links on page to get links on other pages.")
  return Pipulate([
    ('clear', ''),
    ('table', [
      ('url','PreCrawl'),
      (globs.PIPURL, '?')
    ]),
    ('?', ''),
    ('?', ''),
    ('sheet', 'visualizations', [
      ('viewname', 'makeview', 'sharelink', 'datestamp', 'guid', 'includecode', 'compresseddata'),
      ('sitemap', '?', '', '', '', '')
    ]),
    ('?', 'visualizations'),
    ('stop', '')
  ], label='Crawl, 2-Deep')

def PagesTab():
  '''Collect links now residing in Sheet 1 from 2-DEEP crawl and de-dupe URLs into new tab.'''
  out("Collecting links from Sheet 1 and de-duplicating Pages into new tab.")
  pages = set(globs.sheet.col_values(1))
  siteurls = []
  siteurls.append(('URL', 'Archive', 'Title', 'Description', 'MetaKeywords'))
  for apage in pages:
    if apage.lower() != 'url':
      siteurls.append((apage, '?', '?', '?', '?'))
  return Pipulate([
    ('sheet', 'Pages', siteurls)
  ], label='De-duplicating Links')
  #  ('?', 'Pages'),
  #  ('stop', '')

def Cancel():
  '''Go back to default main menu.'''
  out("Cancel")
  return Pipulate()

#                            _             _       _                   Pre-Pipulators may be chosen directly from the
#  _ __  _ __ ___      _ __ (_)_ __  _   _| | __ _| |_ ___  _ __ ___   main menu or secondary. They point to object that
# | '_ \| '__/ _ \____| '_ \| | '_ \| | | | |/ _` | __/ _ \| '__/ __|  are called as functions when the menu option is
# | |_) | | |  __/____| |_) | | |_) | |_| | | (_| | || (_) | |  \__ \  POST'ed. Think of it as the function-hook location
# | .__/|_|  \___|    | .__/|_| .__/ \__,_|_|\__,_|\__\___/|_|  |___/  to do stuff before the normal ?-replacement phase
# |_|                 |_|     |_|                                      begins. They can do anything to the spreadsheet.
def prePipulators():
  return {
    'clear':        ClearSheet1,
    'serps':        SERPTrack,
    'client':       SetupClient,
    'cancel':       Cancel,
    'linksonpage':  LinksOnPage,
    'quickcrawl':   QuickCrawl,
    'linkgraph':    LinkGraph,
    'pagestab':     PagesTab,
    'tests':        RunTests,
    'add':          AddColumns,
    'sitemap':      MakeSitemap,
    'fillmarks':    FillQMarks,
    'resetmarks':   ResetQMarks,
    'repipulate':   RinseAndRepeat,
    'checklist':    SEOChecklist,
    'keywordlist':  KeywordChecklist
  }

def repipulate():
  """Operation bullet-proofing Pipulate begins!"""
  retries = 1
  delay = 10
  for x in range(1, retries+1):
    out("Pipulate Iteration %s" % x)
    if x != 1:
      time.sleep(delay*(x-1))
    for yieldme in Pipulate(label="?-Replacement phase starting: pass #%s of %s..." % (x, retries)):
      if yieldme == ("stop", "", "", ""):
        raise SystemExit
        #pass
      yield yieldme
    if x != retries:
      yme = 'Pausing <span class="countdown">%s</span> seconds before pass #%s of %s.' % (delay*x, x+1, retries)
      yield yme, "Retrying ?-Replacement Phase", "", ""
      yield "countdown", "", "", ""
      yield "", "", "", ""
  yield "Finished!", "Finished!", "", ""
  yield "finished", "", "", ""

def foo():
  return 'bar'
