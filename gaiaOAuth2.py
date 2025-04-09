from flask import Flask, render_template, render_template_string, send_from_directory, request, current_app, send_file, session, redirect, url_for, abort
import requests
import json
import os
import sys
import configparser
from urllib import parse
import array
import zipfile
from datetime import datetime
import jwt
from jwt.exceptions import InvalidTokenError
import calendar
import webbrowser
import time
import shutil

app = Flask(__name__)

configFilePath = './config.cfg'
	
if(os.path.exists(configFilePath) == False):
	print("Configuration file %s is not present. Exiting."%(configFilePath))
	sys.exit()
configuration = configparser.ConfigParser()
configuration.read(configFilePath)

clientId = configuration ['User and Pwd']['clientId']
if(clientId is None):
	print("Client API not set in config file.Exiting.")
	sys.exit()

clientSecret = configuration ['User and Pwd']['clientSecret']
if(clientSecret is None):
	print("Client API password not set in config file.Exiting.")
	sys.exit()

amLocation = configuration ['User and Pwd']['amlocation']
if(amLocation is None):
	print("Location of Account Manager is not set.Exiting.")
	sys.exit()
	
app.secret_key = configuration ['User and Pwd']['secretKey']
if(app.secret_key is None):
	print("Secret key is not set.Exiting.")
	sys.exit()

# The client ID is used by Account Manager to review if the redirect URL is matching any allowed howst.
# To exchange the Code or refresh the token, the password of the ClientID is needed.

token_url = "https://"+amLocation+"/dwsso/oauth2/authorize?client_id="+clientId+"&redirect_uri=http://localhost:3000/redirect&response_type=code"

_offset = 0 #this variable is needed to control the amount of zone retrieved. Salesforce Commerce API eCDN only returns a maximum of 50 zones. It is therefore mandatory to loop over them using a control variable.

def getHeader():
	if(session['access_token']):
		return {'Content-Type':'application/json','User-Agent': 'gaia https://github.com/arouge/gaia/',"Authorization": "Bearer "+session['access_token']}
	else:		
		return "error"

def getUserList(organizationId):
	userList = []
	endpoint = "https://"+amLocation+"/dw/rest/v1/users/search/findAllByOrg?organization="+organizationId
	
	response = requests.get(endpoint, headers=getHeader())
	userJson = response.json()
			
	return userJson

def getOrganization():
	organizationList = []
	endpoint = "https://"+amLocation+"/dw/rest/v1/organizations?size=1000&page=0"
	response = requests.get(endpoint, headers=getHeader())
	if(200 == response.status_code):
		jsonResponse = response.json()
		for eachOrganization in jsonResponse["content"]:
			organizationList.append({
				"id": eachOrganization["id"],
				"name": eachOrganization["name"]
				})
		session['organizations'] = organizationList

def getUserAudit(userId):
	auditList = []

	endpoint = "https://"+amLocation+"/dw/rest/v1/users/"+userId+"/audit-log-records"

	response = requests.get(endpoint, headers=getHeader())
	if(200 == response.status_code):
		auditJson = response.json()
		for eachAuditEntry in auditJson["content"]:
			auditList.append(eachAuditEntry)

	return auditList

def create_folder(path):
    try:
        os.mkdir(path)
        print(f"Folder created successfully : {path}")
    except FileExistsError:
        print(f"The folder already exist: {path}")
    except PermissionError:
        print(f"Not enough permission to create the folder: {path}")
    except Exception as e:
        print(f"Error while creating folder. : {e}")

def compress_directory(source_directory, zip_name=None):
    # If no name is specified, use directory name + timestamp
    if zip_name is None:
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        directory_name = os.path.basename(os.path.normpath(source_directory))
        zip_name = f"{directory_name}_{date_str}.zip"
    
    # Complete path of the zip file
    zip_path = os.path.join(os.path.dirname(source_directory), zip_name)
    
    # Creating the ZIP file
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Browse all files and subdirectories
        for root_folder, subdirectories, files in os.walk(source_directory):
            for file in files:
                # Complete file path
                file_path = os.path.join(root_folder, file)
                # Relative path to preserve folder structure
                relative_path = os.path.relpath(file_path, os.path.dirname(source_directory))
                # Add to ZIP
                zipf.write(file_path, relative_path)
        shutil.rmtree(source_directory)
		
    print(f"Directory successfully compressed: {zip_path}")
	# Delete folder and its content here.
	
    return zip_path
def verify_token_and_redirect():    
    if ('access_token' not in session or 'refresh_token' not in session or
            session['access_token'] is None or session['refresh_token'] is None):
        return 'refreshIsNotPossible'
    
    try:
        epoch_time = int(time.time())
        
        decoded_access = jwt.decode(session['access_token'], options={"verify_signature": False})
        decoded_refresh = jwt.decode(session['refresh_token'], options={"verify_signature": False})

        access_exp = decoded_access["exp"]
        refresh_exp = decoded_refresh["exp"]    

        # Both tokens are expired
        if epoch_time >= access_exp and epoch_time >= refresh_exp:
            session.clear()
            return 'refreshIsNotPossible'
        
        # Access token nearing expiration time but refresh token still valid.
        if (epoch_time + 30 >= access_exp) and (epoch_time < refresh_exp):
            refresh_access_token()
            return 'OK'
        return 'OK'
    
    except (KeyError, jwt.PyJWTError) as e:
        print(f"Error while retrieving tokens.: {str(e)}")
        return 'NOK'
    
def revokeToken():
    revocation_endpoint = "https://"+amLocation + "/dwsso/oauth2/token/revoke"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    access_revoked = False
    try:
        access_data = {
            'token': session['access_token'],
            'token_type_hint': 'access_token',
            'client_id': clientId,
            'client_secret': clientSecret
        }
        
        access_response = requests.post(
            revocation_endpoint,
            data=access_data,
            headers=headers,
            auth=None
        )
        
        access_revoked = access_response.status_code == 200
    except Exception as e:
        print(f"Erreur lors de la révocation de l'access token: {e}")

    refresh_revoked = False
    try:
        refresh_data = {
            'token': session['refresh_token'],
            'token_type_hint': 'refresh_token',
            'client_id': clientId,
            'client_secret': clientSecret
        }
        
        refresh_response = requests.post(
            revocation_endpoint,
            data=refresh_data,
            headers=headers,
            auth=None
        )
        
        refresh_revoked = refresh_response.status_code == 200
    except Exception as e:
        print(f"Erreur lors de la révocation du refresh token: {e}")
    session.clear()
    return access_revoked, refresh_revoked

@app.route('/login-process', methods=['GET', 'POST'])
def login_process():
         return redirect(token_url)
     
@app.route('/logout')
def logout():
    revokeToken()

    #session.clear()
    return redirect('/')

@app.route('/')
def index():
    # Mémoriser le chemin actuel
    session['currentPath'] = '/'

    # Vérifier le token
    test_status = verify_token_and_redirect()
    if 'refreshIsNotPossible' == test_status:
        return render_template('login.html')
    
    if('OK' == test_status):
        decoded_access = jwt.decode(session['access_token'], options={"verify_signature": False})
        username = decoded_access['subname']      
        getOrganization()
        if 'organizations' in session:
	        # Accéder directement au tableau
	        organizations = session['organizations']
        return render_template('index.html', organizations=organizations, user=username)

def check_id_exists(array, id_value):
    for row in array:
        if row["id"] == id_value:  # Checking the id column (index 0)
            return True
    return False

@app.route('/users')
def userList():
    session['currentPath'] = '/userList'

    # Vérifier le token
    test_status = verify_token_and_redirect()
    if 'refreshIsNotPossible' == test_status:
        return redirect(token_url)   

    if ('OK' == test_status):
        decoded_access = jwt.decode(session['access_token'], options={"verify_signature": False})
        username = decoded_access['subname']
        getOrganization()
        userList = []
        organizationList = session['organizations']

        #If direct access to userList endpoint is made without a parameter for organizationId, we redirect the request to the root of the site
	
        if(request.args.get('organizationId') is None):
            return redirect("/")
	
        if(check_id_exists(organizationList, request.args.get('organizationId'))):
            userJson  = getUserList(request.args.get('organizationId'))
        else:
            return redirect("/")

        for eachUser in userJson["content"]:
            userList.append(eachUser)

        return render_template('users.html', users = userList, user=username)

@app.route('/audit')
def retrieveUserAudit():
    session['currentPath'] = '/audit'

	# Vérifier le token
    test_status = verify_token_and_redirect()
    if 'refreshIsNotPossible' == test_status:
        return redirect(token_url)
    if('OK' == test_status):
        getOrganization()
        organizationId = request.args.get('organizationId')

        create_folder(organizationId)

        userList = []
        userJson  = getUserList(organizationId)
        for eachUser in userJson["content"]:
            auditList=[]
            userid= eachUser["id"]
            userAudit = getUserAudit(userid)
            with open(organizationId+"/"+eachUser["mail"]+".xml",'w') as f:
                json.dump(userAudit, f,ensure_ascii=False, indent=2)
        orgPath = organizationId
        compress_directory(orgPath,"static/"+orgPath+".zip")
        return render_template('audit.html', zip_file_url = "/download/"+orgPath+".zip")

@app.route('/download/<filename>')
def download_file(filename):
    # Ensure only zip files can be downloaded
    if not filename.endswith('.zip'):
        abort(404)  # Return 404 if not a zip file
    
    # Check if the file exists in the static folder
    if not os.path.exists(os.path.join(app.static_folder, filename)):
        abort(404)  # Return 404 if file doesn't exist
    
    # Serve the file from the static directory
    return send_from_directory(
        directory=app.static_folder,
        path=filename,
        as_attachment=True  # This will prompt download rather than trying to open in browser
    )

@app.route('/style.css')
def style():
	return current_app.send_static_file('style.css')

@app.route('/redirect')
def exchangecode():
    #Here we verify existence of access_token (which is highly unlikely)
    # We exchange a code granted by Account Manager to get both a refresh token and an access token
    # At the time of writing, access_token as a 30 minutes (1800 seconds) validty while the refresh token
    # has a 24h  (86400 seconds)
	
    session['code'] = request.args.get('code')
    session['client_id'] = request.args.get('client_id')

    exchangeUrl = "https://" + amLocation + "/dwsso/oauth2/access_token"
    
    data = {
        "grant_type": "authorization_code",
        "code": session['code'],
        "redirect_uri": "http://localhost:3000/redirect",
        "client_id": session['client_id'],
		"client_secret": clientSecret
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
	
    response = requests.post(exchangeUrl, data=data, headers=headers)
    if(200 == response.status_code):
        responseJson = response.json()
        session['access_token'] = responseJson["access_token"]
        session['refresh_token'] = responseJson["refresh_token"]

    return redirect(session['currentPath'])

def refresh_access_token():
    refresh_token = session.get('refresh_token')
    if not refresh_token:
        return False, "Aucun refresh token disponible"
    
    refreshUrl = "https://" + amLocation + "/dwsso/oauth2/access_token"
    
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": clientId,
        "client_secret": clientSecret
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        response = requests.post(refreshUrl, data=data, headers=headers)

        if response.status_code == 200:
            response_json = response.json()
            content = response_json.get("content", response_json)  # Utilise directement response_json si pas de clé "content"
            
            # Mettre à jour les tokens dans la session
            session['access_token'] = content.get("access_token")
            
            # Certains serveurs renvoient un nouveau refresh token
            if "refresh_token" in content:
                session['refresh_token'] = content.get("refresh_token")
                
            return 'True', "Token renouvelé avec succès"
        else:
            return False, f"Erreur: {response.status_code}, {response.text}"
            
    except Exception as e:
        return False, f"Exception: {str(e)}"
    
if __name__ == '__main__':
	app.run(host='0.0.0.0', port=3000)
