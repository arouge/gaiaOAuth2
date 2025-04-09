# Gaia OAuth2

Gaia is a Flask-based web application that helps you manage and audit users in Salesforce Commerce Cloud (SFCC) organizations through the Account Manager API. It provides a simple interface to:

1. List organizations
2. View users in an organization
3. Extract audit logs for all users in an organization

## Prerequisites

- Python 3.x
- Flask and dependencies (requests, jwt, etc.)
- Salesforce Commerce Cloud Account Manager access credentials

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/arouge/gaiaOAuth2.git
   cd gaia
   ```

2. Install the required dependencies:
   ```
   pip3 install requirements.txt
   ```

3. Update `config.cfg` file in the root directory with the following structure:
   ```
   [User and Pwd]
   clientId = YOUR_CLIENT_ID
   clientSecret = YOUR_CLIENT_SECRET
   amlocation = YOUR_ACCOUNT_MANAGER_LOCATION
   secretKey = YOUR_SECRET_KEY
   ```

   - `clientId`: Your SFCC API client ID
   - `clientSecret`: Your SFCC API client secret
   - `amlocation`: The Account Manager domain (e.g., `account.demandware.com`)
   - `secretKey`: A random string used for Flask session encryption

## Usage

1. Start the application:
   ```
   python3 gaiaOAuth2.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:3000/
   ```

3. The application will redirect you to the SFCC Account Manager for authentication.

4. After successful authentication, you'll be redirected back to the application.

5. The main page will display a list of organizations you have access to.

6. Click on an organization to view its users.

7. Use the audit function to extract and download audit logs for all users in an organization.

## Application Flow

1. **Authentication**: Uses OAuth2 authorization code flow to obtain access and refresh tokens from SFCC Account Manager.
2. **Token Management**: Automatically refreshes tokens when they expire.
3. **Organization Listing**: Retrieves and displays organizations the authenticated user has access to.
4. **User Listing**: Shows users in a selected organization.
5. **Audit Extraction**: Extracts audit logs for all users in an organization and provides them as a downloadable ZIP file.

## Directory Structure

- `gaiaOAuth2.py`: Main application file
- `config.cfg`: Configuration file (must be created)
- `static/`: Directory for static files and generated ZIP files
- `templates/`: HTML templates (not included in this repository, must be created)

## API Endpoints

- `/`: Main page showing organizations
- `/users`: Lists users in a given organization
- `/audit`: Extracts audit logs for all users in an organization
- `/download/<filename>`: Endpoint to download generated ZIP files
- `/redirect`: OAuth2 callback endpoint
- `/style.css`: Serves CSS styles

## Template Requirements

The application expects the following HTML templates in the `templates` directory:

1. `index.html`: Displays organizations
2. `users.html`: Displays users in an organization  
3. `audit.html`: Displays a download link for audit logs

## Security Features

- JWT token validation
- Token refresh functionality
- Session management
- File download security checks

## Limitations

- The application retrieves a maximum of 1000 organizations at once
- The SFCC API has rate limits that may affect performance with large datasets

## Troubleshooting

1. **Configuration File Missing**: Ensure `config.cfg` exists and has all required fields.
2. **Authentication Failures**: Verify your clientId and clientSecret are correct.
3. **Permission Errors**: Ensure you have proper permissions in SFCC Account Manager.
4. **File Creation Errors**: Check that the application has write permissions for the folders it needs to create.

## Author

[arouge](https://github.com/arouge)
