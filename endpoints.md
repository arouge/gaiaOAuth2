# Account Manager Endpoints

This document lists all the Salesforce B2C Account Manager endpoints used in the gaiaOAuth2 project.

## Authentication Endpoint

```
https://{amlocation}/dwsso/oauth2/authorize
https://{amlocation}/dwsso/oauth2/access_token
```
**Purpose**: Initiates the OAuth2 authorization flow to authenticate the user.  
**Parameters**:
- `client_id`: Your OAuth client ID
- `redirect_uri`: Callback URL (http://localhost:3000/redirect)
- `response_type`: Set to "code" to respect OAuth2 process

## Organization Endpoints

```
https://{amlocation}/dw/rest/v1/organizations
```
**Purpose**: Retrieves a list of all organizations the authenticated user has access to.  
**Parameters**:
- `size`: Maximum number of results (1000)
- `page`: Page number for pagination (0)
**Method**: GET
**Response**: JSON containing organization details including ID and name

## User Endpoints

```
https://{amlocation}/dw/rest/v1/users/search/findAllByOrganization={organizationId}
```
**Purpose**: Retrieves all users belonging to a specific organization.  
**Parameters**:
- `organization`: Organization ID
**Method**: GET
**Response**: JSON containing user details

## Audit Log Endpoints

```
https://{amlocation}/dw/rest/v1/users/{userId}/audit-log-records
```
**Purpose**: Retrieves audit logs for a specific user.  
**Parameters**:
- `userId`: User ID
**Method**: GET
**Response**: JSON containing audit log records
