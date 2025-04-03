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
app.secret_key = "wqgO5k09iu7QSmMlVIG" 

#version="v1" #This variable is used in the http call. To ensure better portability, it has been set as a variable instead of being hard coded.

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

amLocation = configuration ['User and Pwd']['amlocation']
if(amLocation is None):
	print("ALocation os Account Manager is not set.Exiting.")
	sys.exit()


#The client ID is used by Account Manager to review if the redirect URL is matching any allowed howst.

amUrl = "https://"+amLocation+"/dwsso/oauth2/authorize?client_id="+clientId+"&redirect_uri=http://localhost:3000/redirect&response_type=token"

_offset = 0 #this variable is needed to control the amount of zone retrieved. Salesforce Commerce API eCDN only returns a maximum of 50 zones. It is therefore mandatory to loop over them using a control variable.

def getBearerToken():
	webbrowser.open(amUrl)

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
    """
    Vérifie si un token d'accès existe et n'est pas expiré.
    Retourne None si le token est valide, ou une redirection si le token est absent ou expiré.
    """
    # Obtenir le temps EPOCH actuel
    epoch_time = int(time.time())
    
    # Vérifier si un token d'accès existe
    if 'access_token' not in session:
        # Pas de token, rediriger vers l'Account Manager
        return redirect(amUrl)
    
    # Décoder le token JWT sans vérifier la signature
    try:
        decoded_payload = jwt.decode(session['access_token'], options={"verify_signature": False})
        expirationTime = decoded_payload["exp"]
        
        # Vérifier si le token expire dans les 30 prochaines secondes
        if epoch_time + 30 >= expirationTime:
            # Token proche de l'expiration, rediriger
            return redirect(amUrl)
            
        # Token valide
        return None
    except Exception as e:
        # Erreur lors du décodage, le token est peut-être malformé
        app.logger.error(f"Erreur lors du décodage du token: {str(e)}")
        return redirect(amUrl)
    
@app.route('/')
def index():
    # Mémoriser le chemin actuel
    session['currentPath'] = '/'
    
    # Vérifier le token
    redirect_response = verify_token_and_redirect()
    if redirect_response:
        return redirect_response
    
    # Si nous arrivons ici, le token est valide
    #Collecte des organisations disponibles pour l'utilisateur en cours et stockage dans la session.
    #/dw/rest/v1/organizations?size=1000&page=0
    #Nous ne conservons que l'Id et le nom.
    getOrganization()
	
    if 'organizations' in session:
	    # Accéder directement au tableau
	    organizations = session['organizations']
		
    return render_template('index.html', organizations=organizations)

@app.route('/redirect', methods=['GET'])
def redirect_handler():
    #Here we redirect to a server friendly url so the server can process the variable.
	#Instead of have #access_tplem the arguments are not passed with somethiing like ?access_token
	#Endpoint changes to process_token
    
    return render_template('redirect.html')

def check_id_exists(array, id_value):
    for row in array:
        if row["id"] == id_value:  # Checking the id column (index 0)
            return True
    return False

@app.route('/users')
def userList():
	session['currentPath'] = '/userList'
	redirect_response = verify_token_and_redirect()
    
	if redirect_response:
		return redirect_response

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

	return render_template('dashboard.html', users = userList)

@app.route('/audit')
def retrieveUserAudit():
	session['currentPath'] = '/audit'

	redirect_response = verify_token_and_redirect()
	if redirect_response:
		return redirect_response
	
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
def flask_logo():
	return current_app.send_static_file('style.css')

@app.route('/process_token')
def process_token():	
	#Ici, intégrer les éléments du token dans la session.
    session['access_token'] = request.args.get('access_token')

    decoded_payload = jwt.decode(session['access_token'], options={"verify_signature": False})
    expirationTime = decoded_payload["exp"]
	
    if(session['currentPath'] is None):
        session['currentPath'] = "/"
	
    return redirect(session['currentPath'])

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=3000)
