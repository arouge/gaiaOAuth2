# gaiaOAuth2

## Description
gaiaOAuth2 is a management tool for Salesforce B2C Account Manager that allows administrators to connect via OAuth2 to perform scripted management operations, including:

- Listing available organizations
- Viewing users within an organization
- Extracting user audit logs
- Generating and downloading ZIP archives containing audit data in XML format

This project is at very early stage and is more a place holder for ideas so the community can share their need and how they would like to implement them, I (Alex Rouge) have created this project in the hope it helps both the community. In the actual state, this flask project is not ready to be productize. To deploy in production, a nginx server deployement is needed but this goes beyond the scope of this project.

## Features

- **OAuth2 Authentication**: Secure connection to Salesforce B2C Account Manager
- **Organization Management**: View and select organizations associated with your account
- **User Management**: List users within an organization
- **Audit Extraction**: Generate audit reports for all users in an organization
- **Data Export**: Export audit logs in XML format, compressed into a ZIP file

## Requirements

- Python 3.x
- Flask
- Additional Python modules (see Installation section)
- Salesforce B2C Account Manager account with API access rights
- OAuth2 Client ID configured in Account Manager

## Installation

1. Clone this repository:
```bash
git clone https://github.com/arouge/gaiaOAuth2.git
cd gaiaOAuth2
```

2. Install the required dependencies:
```bash
pip3 install requirements.txt 
```

3. Update the configuration file `config.cfg` in the project root with the following content:
```ini
[User and Pwd]
clientId = your_client_id
amlocation = account-manager-domain.com
secretKey = a_secret_to_secure_sessions_data
```

## Configuration

You need to configure the following items in the `config.cfg` file:

- `clientId`: The OAuth2 client identifier obtained from Salesforce B2C Account Manager
- `amlocation`: The URL of your Account Manager instance (without https://)
- `secretKey`: A secret key used to secure the Flask session and encrypt sensitive data

Additionally, ensure that the following redirect URL is authorized in your OAuth2 configuration in Account Manager:
```
http://localhost:3000/redirect
```

## Usage

1. Start the application:
```bash
python3 gaiaOAuth2.py
```

2. Access the application via your browser:
```
http://localhost:3000
```

3. You will be automatically redirected to the Salesforce B2C Account Manager authentication page.

4. Once authenticated, you can:
   - View the list of organizations you have access to
   - Select an organization to see its users
   - Generate and download audits for all users in an organization

## File Structure

- `gaiaOAuth2.py`: Main Flask application
- `config.cfg`: Configuration file (to be created)
- `templates/`: Folder containing HTML templates
- `static/`: Folder for CSS files and generated ZIP archives

## Security

- The application uses OAuth2 for authentication
- JWT tokens are verified with each request
- Expired tokens are automatically detected, requiring reauthentication
- Verification of the validity of parameters provided in URLs

## Limitations

- The application is designed to work on localhost on port 3000
- A maximum of 1000 organizations can be displayed
- Audit log archives are temporarily stored in the `static/` folder

## Contribution

Contributions are welcome! Feel free to submit pull requests or open issues to improve this tool.
