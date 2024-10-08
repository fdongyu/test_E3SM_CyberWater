import requests
import struct
import time 
import os
import ssl

cert_path = "/global/homes/a/amlodha/Final_Data_Exchange_Service_Code1/src/clients/cyberwater/lib/ssl-cert-snakeoil.pem"

def create_session(server_url, source_model_ID, destination_model_ID, initiator_id, invitee_id,
                   input_variables_ID=None, input_variables_size=None,
                   output_variables_ID=None, output_variables_size=None):
    """
    Creates a session with specified parameters on the server.

    Parameters:
        server_url (str): The server URL.
        source_model_ID (int): ID of the source model.
        destination_model_ID (int): ID of the destination model.
        initiator_id (int): ID of the session initiator.
        inviter_id (int): ID of the inviter.
        input_variables_ID (list): Optional list of input variable IDs.
        input_variables_size (list): Optional list of sizes for input variables.
        output_variables_ID (list): Optional list of output variable IDs.
        output_variables_size (list): Optional list of sizes for output variables.

    Returns:
        dict: JSON response from the server or an error message.
    """
    # Prepare data for the POST request
    data = {
        "source_model_ID": source_model_ID,
        "destination_model_ID": destination_model_ID,
        "initiator_id": initiator_id,
        "invitee_id": invitee_id,
        "input_variables_ID": input_variables_ID or [],
        "input_variables_size": input_variables_size or [],
        "output_variables_ID": output_variables_ID or [],
        "output_variables_size": output_variables_size or []
    }


    # Send POST request to the server
    response = requests.post(f"{server_url}/create_session", json=data, verify=False)
    
    # Check response status
    if response.ok:
        session_info = response.json()
        print(f"Session status: {session_info.get('status', 'unknown')}. Session ID: {session_info.get('session_id', 'N/A')}")
        return session_info
    else:
        print("Error occurred:", response.text)
        return {"error": response.text}

def get_session_status(server_url, session_id):
    """
    Client-side function to retrieve the status of a session from the server.

    Parameters:
        server_url (str): The base URL of the server.
        session_id (str): The ID of the session to check.

    Returns:
        The status of the session as an integer if successful, or None if an error occurs.
    """
    # Construct the URL for the GET request
    url = f"{server_url}/get_session_status?session_id={session_id}"
    
    # Send the GET request to the server
    response = requests.get(url, verify=False)
    
    # Check the response status
    if response.ok:
        # Extract the session status from the JSON response
        session_status = response.json()
        return session_status
    else:
        # Optionally handle different error codes distinctly if needed
        print(f"Failed to retrieve session status. Server responded with: {response.status_code} - {response.text}")
        return None

def join_session(server_url, session_id, invitee_id):
    """
    Attempts to join a session with a given session ID and invitee ID.
    
    Parameters:
        server_url (str): The server URL.
        session_id (str): The ID of the session to join.
        invitee_id (int): The invitee ID to authenticate the joining.
        
    Returns:
        dict: A dictionary with 'success' status and 'error' message if applicable.
    """
    data = {"invitee_id": invitee_id, "session_id": session_id}

    try:
        response = requests.post(f"{server_url}/join_session", json=data, verify=False)
        if response.ok:
            return {'success': True}
        else:
            return {'success': False, 'error': response.json().get('detail', 'Unknown error')}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_variable_size(server_url, session_id, var_id):
    """
    Retrieves the size of a specific variable within a session from the server.

    Parameters:
        server_url (str): The server URL.
        session_id (str): The ID of the session.
        var_id (int): The ID of the variable.

    Returns:
        int: The size of the variable if the request is successful, -1 otherwise.
    """
    # Construct the URL and set parameters for the GET request
    url = f"{server_url}/get_variable_size"
    params = {'session_id': session_id, 'var_id': var_id}

    # Perform the GET request
    response = requests.get(url, params=params)
    if response.ok:
        # Parse and return the size from the JSON response
        size_info = response.json()
        print(f"Size of variable {var_id} in session {session_id}: {size_info.get('size', 'Unknown')}")
        return size_info.get('size', -1)
    else:
        # Log and return -1 if there was an error during the request
        print("Error occurred while retrieving variable size:", response.text)
        return -1
    
def send_data(server_url, session_id, var_id, data):
    """
    Sends a list of double precision floats as binary data to the server for a specific session and variable.

    Parameters:
        server_url (str): The server URL.
        session_id (str): The session ID to which the data belongs.
        var_id (int): The identifier for the variable to which the data is related.
        data (list of float): The data to be sent, represented as a list of doubles.

    Note:
        The data is packed in little-endian format.
    """
    # Convert the list of doubles into binary data using little-endian format
    binary_data = struct.pack('<' + 'd' * len(data), *data)

    # Prepare HTTP headers to include session and variable identifiers
    headers = {
        'Session-ID': session_id,
        'Var-ID': str(var_id)
    }

    # Send the binary data as a POST request to the server
    response = requests.post(f"{server_url}/send_data", data=binary_data, headers=headers, verify=False)
    
    return response


def get_variable_flag(server_url, session_id, var_id):
    """
    Retrieves the flag status for a specific variable within a session.

    Parameters:
        server_url (str): The server URL.
        session_id (str): The ID of the session.
        var_id (int): The ID of the variable.

    Returns:
        int: The flag status if the request is successful, None otherwise.
    """
    # Construct the URL and set parameters for the GET request
    url = f"{server_url}/get_variable_flag"
    params = {'session_id': session_id, 'var_id': var_id}

    # Perform the GET request
    response = requests.get(url, params=params, verify=False)

    # Check if the request was successful
    if response.ok:
        # Parse and return the flag status from the JSON response
        flag_status = response.json().get('flag_status')
        print(f"Flag for session {session_id} variable {var_id}: {flag_status}")
        return flag_status
    else:
        # Log and return None if there was an error during the request
        print("Error occurred while retrieving flag status:", response.text)
        return None


def receive_data(server_url, session_id, var_id):
    """
    Receives binary data from the server for a given session and variable ID, assuming the data
    is a stream of double precision floats.

    Parameters:
        server_url (str): The server URL.
        session_id (str): The session ID from which data is to be retrieved.
        var_id (int): The variable ID associated with the data.
    
    Returns:
        list of float: The unpacked data array of double precision floats, or None if an error occurred.
    """
    params = {"session_id": session_id, "var_id": var_id}

    response = requests.get(f"{server_url}/receive_data", params=params, verify=False)

    if response.ok:
        binary_data = response.content
        num_doubles = len(binary_data) // 8  # Each double is 8 bytes
        unpacked_data = struct.unpack(f'<{num_doubles}d', binary_data)
        print(f"Received binary data of length {num_doubles}")
        print("Data array:", unpacked_data)
        return unpacked_data
    else:
        print("Error retrieving data:", response.text)
        return None
    
def end_session(server_url, session_id, user_id):
    """
    Ends a session on the server using a POST request with the session ID and user ID.
    
    Parameters:
        server_url (str): The server URL.
        session_id (str): The ID of the session to be ended.
        user_id (int): The ID of the user (initiator or invitee) ending the session.
    """
    print(session_id)
    # Prepare data payload for the POST request
    data = {
        "session_id": session_id,
        "user_id": user_id
    }

    # Send the POST request to end the session
    response = requests.post(f"{server_url}/end_session", json=data, verify=False)

    # Check if the request was successful
    if response.ok:
        # Print the status message from the response
        print(response.json().get("status", "No status message received."))
    else:
        # Print an error message if the request failed
        print("Error ending session:", response.text)
