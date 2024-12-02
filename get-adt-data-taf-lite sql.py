# import python modules 
import requests
import datetime
import urllib3
import json
import mariadb
import re
import config
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# MariaDB connection parameters
conn_params= {
    "user" : config.db_user,
    "password" : config.db_password,
    "host" : config.db_host,
    "database" : config.database
}

# Establish database connection
connection= mariadb.connect(**conn_params)
cursor= connection.cursor()

# NetBrain Login script

body = {
    "username" : config.nb_user,      
    "password" : config.nb_password 
}

nb_url = config.nb_url         

# Set proper headers
headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}    
login_url = "/ServicesAPI/API/V1/Session"




def get_compliance_result(result_message):
    # Get PASS/FAIL value from NI result message
    compliance_result_regex = re.compile(r'\[(\S+)\]')
    result_message = re.search(compliance_result_regex, result_message)
    return result_message[1]

def get_rulename(full_rulename):
    # Parse out rulename from NI name
    rulename_regex = re.compile(r'(.+)\s--')
    rulename = re.search(rulename_regex, full_rulename)
    return rulename[1]

def get_ni_ids(adt_row):
    # Get ID value of NIs that were executed in the ADT
    ni_id_list = []
    for cell in adt_row:
        if "id" in cell:
            ni_id_list.append(cell["id"])
    return ni_id_list
        

def add_data(timestamp, device, rulename, status, result):
    # Add result to database function
    try:
        statement = """INSERT INTO results(time, device, rulename, status, result) VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE time=%s, status=%s, result=%s"""
        data = (timestamp, device, rulename, status, result, timestamp, status, result)
        cursor.execute(statement, data)
        connection.commit()
        print(f"Successfully added entry to database {timestamp} | {device} | {rulename}")
    except mariadb.Error as e:
        print(f"Error adding entry to database {timestamp} | {device} | {rulename}: {e}")



try:
    # Do the HTTP request
    response = requests.post(nb_url + login_url, headers=headers, data = json.dumps(body), verify=False)
    # Check for HTTP codes other than 200
    if response.status_code == 200:
        # Decode the JSON response into a dictionary and use the data
        js = response.json()
        # Put token into variable to use later
        token = js['token']
        headers["Token"] = token
        #print (js)
    else:
        print ("Get token failed! - " + str(response.text))
except Exception as e:
    print (str(e))


# Set Tenant and Domain
set_domain_url = "/ServicesAPI/API/V1/Session/CurrentDomain"

body = {
    "domainId": config.domainID,
    "tenantId": config.tenantID
}

try:
    # Do the HTTP request
    response = requests.put(nb_url + set_domain_url, data=json.dumps(body), headers=headers, verify=False)
    # Check for HTTP codes other than 200
    if response.status_code == 200:
        # Decode the JSON response into a dictionary and use the data
        result = response.json()
        #print ("Set domain result: ")
        #print (result)
    elif response.status_code != 200:
        print ("Set Tenant Failed - " + str(response.text))

except Exception as e: 
    print (str(e))


adt_url = "/ServicesAPI/API/V3/TAF/Lite/adt/data"

payload = {
    "endpoint": "T10000J",
    "passkey": "Abcd1234!"
}


try:
    # Do the HTTP request
    response = requests.post(nb_url + adt_url, data=json.dumps(payload), headers=headers, verify=False)
    # Check for HTTP codes other than 200
    if response.status_code == 200:
        # Decode the JSON response into a dictionary and use the data
        result = response.json()
        #print ("Set domain result: ")
        #print(json.dumps(result, indent=4))
    elif response.status_code != 200:
        print ("Get ADT data failed - " + str(response.text))

except Exception as e: 
    print (str(e))

# Local Compliance results for testing/debugging
compliance_results = []

# Loop through ADT table row by row
for row in result["rows"]:
    devicename = row[1]["value"]
    intentIDs = get_ni_ids(row)

    dev_compliance_results = {
        "device": devicename,
        "rules": []
    }

    # Loop through executed Intents in the table
    for intentID in intentIDs:
        ni_result_url = "/ServicesAPI/API/V3/CMDB/NI/result"
        
        ni_result_body = {
            "niIdOrPath": intentID,
            "output": [1] # Results return type (list including what result types you want)
        }
        
        rules_results_list = []

        # Get details of executed intent to populate database
        if intentID != "":
            try:
                # Do the HTTP request
                response = requests.post(nb_url + ni_result_url, data=json.dumps(ni_result_body), headers=headers, verify=False)
                # Check for HTTP codes other than 200
                if response.status_code == 200:
                    # Decode the JSON response into a dictionary and use the data
                    result = response.json()
                    #print (json.dumps(result, indent=4))
                elif response.status_code != 200:
                    print ("Get NI Result failed - " + str(response.text))

            except Exception as e: 
                print (str(e))

            # Parse Intent results and format to store in database
            if result["statusCodes"] != []: # Check for intents with empty status codes
                
                timestamp = datetime.datetime.fromisoformat(result["timePoint"])

                #print(f"Adding {timestamp.strftime("%Y-%m-%d %H:%M:%S")} | {devicename} | {get_rulename(result["niName"])}")

                timestamp_sql = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                rulename = get_rulename(result["niName"])
                status = get_compliance_result(result["statusCodes"][0])
                result_message = result["statusCodes"][0]

                # Add entry to local dict
                rules_result = {
                    "rulename": rulename,
                    "timestamp": timestamp_sql,
                    "status": status,
                    "result": result_message
                }

                dev_compliance_results['rules'].append(rules_result)

                # Write entry to database
                add_data(timestamp_sql, devicename, rulename, status, result_message)
        
    compliance_results.append(dev_compliance_results)


# Close Database connection
cursor.close()
connection.close()

#print(json.dumps(compliance_results, indent=4))