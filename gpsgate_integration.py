#!/usr/bin/env python3
"""
GpsGate to VP Desk 9 Integration
Complete workflow: Fetch data from GpsGate, transform it, and send to VP Desk 9
"""

import requests
import json
from datetime import datetime

# ============================================================================
# CONFIGURATION - Replace with your actual credentials
# ============================================================================
GPSGATE_API_TOKEN = "v2:MDAwMDAwMDAwODplOTRjMGEwZDNlMTAxMmJhMDJiMQ=="  # Replace with your actual GpsGate token
GPSGATE_BASE_URL = "https://terrasport.gpsgate.com/comGpsGate/api/v.1"

VPDESK_API_KEY = "101d9a87-da95-b528-bc70-66994dd887e3"  # Replace with your actual VP Desk 9 API key
VPDESK_BASE_URL = "http://b167-s10/vplanning/api/v2"
VPDESK_RESOURCE_UID = "CAB9-A6A7-6B20-5667-49A7-EDD0-1C31-DA77"  # The resource to update

# ============================================================================
# STEP 1 & 2: Authenticate with GpsGate API and fetch user data
# ============================================================================
def fetch_gpsgate_user(application_id, user_id):
    """
    Authenticate with GpsGate API and fetch user data including position.
    
    Args:
        application_id: The GpsGate application ID
        user_id: The user ID to fetch
        
    Returns:
        dict: User data from GpsGate API, or None if failed
    """
    # Construct the API endpoint URL
    url = f"{GPSGATE_BASE_URL}/applications/{application_id}/users/{user_id}"
    
    # Set up headers with authentication
    headers = {
        "Authorization": GPSGATE_API_TOKEN,
        "Accept": "application/json"
    }
    
    # Add query parameters
    params = {
        "Identifier": "UserId"
    }
    
    print(f"[STEP 1-2] Fetching user data from GpsGate...")
    print(f"           URL: {url}")
    
    try:
        # Make the API request
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        # Check if request was successful
        if response.status_code == 200:
            print("           ✓ SUCCESS: Data retrieved from GpsGate")
            user_data = response.json()
            return user_data
        else:
            print(f"           ✗ ERROR: Request failed with status code {response.status_code}")
            print(f"           Response: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("           ✗ ERROR: Request timed out")
        return None
    except requests.exceptions.ConnectionError:
        print("           ✗ ERROR: Connection error - check your internet connection")
        return None
    except requests.exceptions.RequestException as e:
        print(f"           ✗ ERROR: Request failed: {str(e)}")
        return None
    except json.JSONDecodeError:
        print("           ✗ ERROR: Failed to parse JSON response")
        print(f"           Response: {response.text}")
        return None


# ============================================================================
# STEP 3: Transform GpsGate data to VP Desk 9 format
# ============================================================================
def transform_to_vpdesk_format(gpsgate_data):
    """
    Transform GpsGate user data to VP Desk 9 resource format.
    
    Args:
        gpsgate_data: User data from GpsGate API
        
    Returns:
        dict: Transformed data in VP Desk 9 format, or None if transformation failed
    """
    print("[STEP 3] Transforming data to VP Desk 9 format...")
    
    try:
        # Extract position data from GpsGate response
        track_point = gpsgate_data.get("trackPoint", {})
        position = track_point.get("position", {})
        
        latitude = position.get("latitude")
        longitude = position.get("longitude")
        
        # Validate that we have coordinates
        if latitude is None or longitude is None:
            print("         ✗ ERROR: Missing latitude or longitude in GpsGate data")
            return None
        
        # Create the location string in format "latitude,longitude"
        location_string = f"{latitude},{longitude}"
        
        # Build VP Desk 9 request body
        vpdesk_data = {
            "attributes": [
                {
                    "entityValue": location_string,
                    "entityName": "Collaborateurs-Localisation"
                }
            ],
            "resourceModel": "Collaborateurs"
        }
        
        print(f"         ✓ SUCCESS: Transformed coordinates to: {location_string}")
        return vpdesk_data
        
    except Exception as e:
        print(f"         ✗ ERROR: Transformation failed: {str(e)}")
        return None


# ============================================================================
# STEP 4 & 5: Authenticate with VP Desk 9 and send transformed data
# ============================================================================
def send_to_vpdesk(vpdesk_data, resource_uid):
    """
    Send transformed data to VP Desk 9 API to update resource location.
    
    Args:
        vpdesk_data: Transformed data in VP Desk 9 format
        resource_uid: The UID of the resource to update
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Construct the API endpoint URL
    url = f"{VPDESK_BASE_URL}/resources/{resource_uid}"
    
    # Set up headers with authentication
    headers = {
        "apikey": VPDESK_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    print(f"[STEP 4-5] Sending data to VP Desk 9...")
    print(f"           URL: {url}")
    print(f"           Payload: {json.dumps(vpdesk_data, indent=2)}")
    
    try:
        # Make the PUT request
        response = requests.put(url, headers=headers, json=vpdesk_data, timeout=30)
        
        # Check if request was successful
        if response.status_code in [200, 201, 204]:
            print(f"           ✓ SUCCESS: Location updated in VP Desk 9 (Status: {response.status_code})")
            if response.text:
                print(f"           Response: {response.text}")
            return True
        else:
            print(f"           ✗ ERROR: Request failed with status code {response.status_code}")
            print(f"           Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("           ✗ ERROR: Request timed out")
        return False
    except requests.exceptions.ConnectionError:
        print("           ✗ ERROR: Connection error - check VP Desk 9 URL and network")
        return False
    except requests.exceptions.RequestException as e:
        print(f"           ✗ ERROR: Request failed: {str(e)}")
        return False


# ============================================================================
# STEP 6: Error handling and logging
# ============================================================================
def log_sync_result(success, gpsgate_data=None, error_message=None):
    """
    Log the result of the synchronization operation.
    
    Args:
        success: Boolean indicating if sync was successful
        gpsgate_data: The original GpsGate data (optional)
        error_message: Error message if sync failed (optional)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if success:
        location = "Unknown"
        if gpsgate_data:
            track_point = gpsgate_data.get("trackPoint", {})
            position = track_point.get("position", {})
            lat = position.get("latitude", "?")
            lon = position.get("longitude", "?")
            location = f"{lat},{lon}"
        
        log_entry = f"[{timestamp}] ✓ SUCCESS: Synced location {location}"
        print(f"\n[STEP 6] {log_entry}")
    else:
        log_entry = f"[{timestamp}] ✗ FAILED: {error_message or 'Unknown error'}"
        print(f"\n[STEP 6] {log_entry}")
    
    # Append to log file
    try:
        with open("sync_log.txt", "a") as f:
            f.write(log_entry + "\n")
    except Exception as e:
        print(f"[STEP 6] Warning: Could not write to log file: {str(e)}")


# ============================================================================
# MAIN INTEGRATION WORKFLOW
# ============================================================================
def sync_gpsgate_to_vpdesk(application_id, user_id, resource_uid):
    """
    Complete workflow: Fetch from GpsGate, transform, and send to VP Desk 9.
    
    Args:
        application_id: GpsGate application ID
        user_id: GpsGate user ID
        resource_uid: VP Desk 9 resource UID
        
    Returns:
        bool: True if entire workflow succeeded, False otherwise
    """
    print("\n" + "=" * 70)
    print("GPSGATE TO VP DESK 9 SYNCHRONIZATION")
    print("=" * 70)
    
    # Step 1-2: Fetch data from GpsGate
    gpsgate_data = fetch_gpsgate_user(application_id, user_id)
    if not gpsgate_data:
        log_sync_result(False, error_message="Failed to fetch data from GpsGate")
        return False
    
    # Step 3: Transform data
    vpdesk_data = transform_to_vpdesk_format(gpsgate_data)
    if not vpdesk_data:
        log_sync_result(False, gpsgate_data, "Failed to transform data")
        return False
    
    # Step 4-5: Send to VP Desk 9
    success = send_to_vpdesk(vpdesk_data, resource_uid)
    
    # Step 6: Log result
    if success:
        log_sync_result(True, gpsgate_data)
    else:
        log_sync_result(False, gpsgate_data, "Failed to send data to VP Desk 9")
    
    return success

def main():
    """Main function to run the complete integration"""
    
    # Configuration for your specific setup
    gpsgate_application_id = 3
    gpsgate_user_id = 9
    vpdesk_resource_uid = VPDESK_RESOURCE_UID
    
    # Run the complete synchronization
    success = sync_gpsgate_to_vpdesk(
        application_id=gpsgate_application_id,
        user_id=gpsgate_user_id,
        resource_uid=vpdesk_resource_uid
    )
    
    # Final result
    print("\n" + "=" * 70)
    if success:
        print("✓ COMPLETE: All steps executed successfully!")
        print("  Location data has been synced from GpsGate to VP Desk 9")
    else:
        print("✗ FAILED: Synchronization incomplete. Check errors above.")
        print("  Please verify your API credentials and configuration.")
    print("=" * 70 + "\n")
    
    return success


if __name__ == "__main__":
    main()
