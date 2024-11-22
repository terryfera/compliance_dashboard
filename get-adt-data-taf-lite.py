# import python modules 
import requests
import datetime
import urllib3
import json
import influxdb_client
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Login script

body = {
    "username" : "terry-api",      
    "password" : "BQW*guc*fwd5jda9gck"  
}

nb_url = "https://nblive2024.netbrain.com"          

# Set proper headers
headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}    
login_url = "/ServicesAPI/API/V1/Session"

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
    "domainId": "debe8ad8-debd-452b-b847-049c603fe3b8",
    "tenantId": "55cb871e-e94c-4456-9578-056be4622dd4"
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
        #print (result)
    elif response.status_code != 200:
        print ("Get ADT data failed - " + str(response.text))

except Exception as e: 
    print (str(e))


#print(json.dumps(result, indent=4))

compliance_results = []

for row in result["rows"]:
    devicename = row[1]["value"]
    intentID = row[3]["id"]

    ni_result_body = {
        "niIdOrPath": intentID,
        "output": [1]
    }

    ni_result_url = "/ServicesAPI/API/V3/CMDB/NI/result"
    #print(devicename + " - " + intentID)
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

        #print(devicename + " - " + result["statusCodes"]))

        timestamp = datetime.datetime.fromisoformat(result["timePoint"])

        
        
        dev_compliance_results = {
            "device": devicename,
            "rulename": result["niName"],
            "timestamp": timestamp.strftime("%b %d %Y %H:%M:%S %Z"),
            "result": result["statusCodes"]
        }

        compliance_results.append(dev_compliance_results)


print(json.dumps(compliance_results, indent=4))