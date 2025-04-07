from typing import Any, Dict, List, Optional, Union
import requests
from requests.auth import HTTPBasicAuth

def get_oauth_token(
    client_id: str,
    client_secret: str,
    token_url: str
) -> str:
    """
    Retrieves an OAuth token using the client credentials grant type.

    Args:
        client_id (str): The client ID.
        client_secret (str): The client secret.
        token_url (str): The token URL.

    Returns:
        str: The access token.
    """
    auth = HTTPBasicAuth(client_id, client_secret)
    data = {
        'grant_type': 'client_credentials'
    }
    response = requests.post(token_url, auth=auth, data=data)
    response.raise_for_status() 
    token_info = response.json()
    return token_info['access_token']

def get_salesforce_oauth_token(
    client_id: str,
    client_secret: str,
    token_url: str,
    username: str,
    password: str
) -> str:
    """
    Retrieves an OAuth token using the client credentials grant type.

    Args:
        client_id (str): The client ID.
        client_secret (str): The client secret.
        token_url (str): The token URL.

    Returns:
        str: The access token.
    """
    data = {
        'grant_type': 'password',
        'client_id' : client_id,
        'client_secret' : client_secret,
        'username' : username,
        'password' : password
    }
    response = requests.post(token_url,data=data)
    response.raise_for_status() 
    token_info = response.json()
    return token_info['access_token'], token_info['instance_url']

def make_api_call(
    url: str,
    method: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Union[str, List[str]]]] = None,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Makes an API call to the specified URL with optional headers and parameters.

    Args:
        url (str): The URL to make the API call to.
        method (str): The HTTP method to use, either 'get' or 'post'.
        headers (Optional[Dict[str, str]]): The headers to include in the API call. Defaults to None.
        params (Optional[Dict[str, Union[str, List[str]]]]): The parameters to include in the API call. Defaults to None.
        data (Optional[Dict[str, Any]]): The data to include in the API call (for POST requests). Defaults to None.

    Returns:
        Dict[str, Any]: The JSON response from the API call.

    Raises:
        requests.exceptions.HTTPError: If the API call returns a non-success status code.
    """
    if method.upper() == 'GET':
        response = requests.get(url, headers=headers, params=params)
    elif method.upper() == 'POST':
        response = requests.post(url, headers=headers, params=params, json=data)
    else:
        raise ValueError("Invalid method. Must be 'get' or 'post'")
    response.raise_for_status()
    return response.json()

