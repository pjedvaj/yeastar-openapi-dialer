import requests
import json
import os



# Yeastar P-Series PBX System API: https://help.yeastar.com/en/p-series-appliance-edition/developer-guide/about-this-guide.html



path = os.getcwd() + '\\'

address = 'https://192.168.1.200:8088'



# API AUTHENTICATION



# Get access token (valid for 30 minutes)

getTokenUrl = f'{address}/openapi/v1.0/get_token'

try:
    token_file = open(path + 'token.json', mode='r')
    token = json.load(token_file)
    # print(f'token: {token}')
    token_file.close()
except FileNotFoundError:
    print('Datoteka token.json ne postoji')

loginResponse = requests.post(getTokenUrl, json = token, verify=False)

response = loginResponse.json()
# print(response)

access_token = response['access_token']
# print(f'Access token: {access_token}')



# Get refresh token (valid for 1 day)

refresh_token = response['refresh_token']
# print(f'Refresh token: {refresh_token}')

refreshTokenUrl = f'{address}/openapi/v1.0/openapi/v1.0/refresh_token'

refresh = {
	"refresh_token": f"{refresh_token}"
}

refreshResponse = requests.post(refreshTokenUrl, json = refresh, verify=False)



# SHOW ALL AVAILABLE EXTENSIONS



# Show only online and available extensions

extensionsUrl = f'{address}/openapi/v1.0/extension/list?page=1&page_size=50&sort_by=number&order_by=asc&access_token={access_token}'

extensionsResponse = requests.get(extensionsUrl, verify=False)

availableExtensions = extensionsResponse.json()

availableList = []

available = availableExtensions['data']
# print(f'available: {available}')

for i in range(len(available)):
    if (available[i]['presence_status'] == 'available' and available[i]['online_status']['linkus_desktop']['status'] == 1
    or available[i]['online_status']['linkus_web']['status'] == 1
    or available[i]['online_status']['linkus_mobile']['status'] == 1 or available[i]['online_status']['sip_phone']['status'] == 1):
        availableList.append(available[i]['number'])

print(f'Available extensions: {availableList}')



# COMPARE LIST OFF AGENTS AND ALL AVAILABLE EXTENSIONS



agents = ['201']

freeAgent = list(set(agents) & set(availableList))

print(f'free agents: {freeAgent}')



# Load phone number list from file

try:
    numberList_file = open(path + 'list.txt', mode='r')
    list = numberList_file.read()
    numberList = list.split('\n')
    print(f'Number list: {numberList}')
    numberList_file.close()
except FileNotFoundError:
    print('File list.txt does not exist.')



# Dialer to make a call

dialerUrl = f'{address}/openapi/v1.0/call/dial?access_token={access_token}'

for i in range(len(numberList)):

    dial = {
        "caller": f"{freeAgent[i]}",
        "callee": f"{numberList[i]}",
        "auto_answer": "yes"
    }

    dialResponse = requests.post(dialerUrl, json = dial, verify=False)
    # print(f'dial response: {dialResponse}')