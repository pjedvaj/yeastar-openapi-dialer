import requests
import json
import time
import os



# Yeastar P-Series PBX System API: https://help.yeastar.com/en/p-series-appliance-edition/developer-guide/about-this-guide.html



path = os.getcwd() + '\\'

address = 'https://192.168.1.200:8088'

dialer = '100' # Must be logined into Linkus desktop application

queue = '640' # Queue number



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



# SHOW AGENTS LOGGED IN TO QUEUE (DOESN'T WORK)



# now = time.strftime('%d/%m/%G %H:%M:%S', time.localtime()) # Format: 06/12/2022 12:20:49 (must be identical to PBX settings or no results will show)

# print(f'Timestamp: {now}')

# queueUrl = f'{address}/openapi/v1.0/call_report/list?type=queueagentlogintime&start_time=06/12/2022 12:20:49&end_time={now}&queue_id=1&ext_id_list=50&access_token={access_token}'

# queueResponse = requests.get(queueUrl, verify=False)

# queue = queueResponse.json()

# print(f'queue: {queue}')



# SHOW ALL AVAILABLE EXTENSIONS



# Show only online and available extensions

# extensionsUrl = f'{address}/openapi/v1.0/extension/list?page=1&page_size=50&sort_by=number&order_by=asc&access_token={access_token}'

# extensionsResponse = requests.get(extensionsUrl, verify=False)

# availableExtensions = extensionsResponse.json()

# availableList = []

# available = availableExtensions['data']
# # print(f'available: {available}')

# for i in range(len(available)):
#     if (available[i]['presence_status'] == 'available' and available[i]['online_status']['linkus_desktop']['status'] == 1
#     or available[i]['online_status']['linkus_web']['status'] == 1
#     or available[i]['online_status']['linkus_mobile']['status'] == 1 or available[i]['online_status']['sip_phone']['status'] == 1):
#         availableList.append(available[i]['number'])

# print(f'Available extensions: {availableList}')



# COMPARE QUEUE AND ALL AVAILABLE EXTENSIONS TO GET QUEUE STATUS (IF NO ONE IS AVAILABLE DON'T MAKE ANY EXTERNAL CALLS)



# freeAgent = list(set(queue) & set(availableList))

# print(f'free agents: {freeAgent}')

# if len(freeAgent) == 0:
#     time.sleep(60)



# CALLING



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
        "caller": f"{dialer}",
        "callee": f"{numberList[i]}",
        "auto_answer": "yes"
    }

    dialResponse = requests.post(dialerUrl, json = dial, verify=False)
    # print(f'dial response: {dialResponse}')



    # Query call to get Call ID

    reportUrl = f'{address}/openapi/v1.0/call/query?access_token={access_token}&from={dialer}'

    reportResponse = requests.get(reportUrl, verify=False)

    report = reportResponse.json()
    # print(f'report: {report}')

    call_id = report['data'][0]['call_id']
    print(f'Call ID: {call_id}')



    # Query call to get Channel ID

    time.sleep(10) # You need to wait few seconds to get Channel ID, 10s here is an example (3s is enough)

    channelUrl = f'{address}/openapi/v1.0/call/query?access_token={access_token}&call_id={call_id}'

    channelResponse = requests.get(channelUrl, verify=False)

    channel = channelResponse.json()
    print(f'channel: {channel}')

    channel_id = channel['data'][0]['members'][1]['outbound']['channel_id'] # Channel ID must be from the dialed number, 'outbound' will be 'extension' for internal calls
    print(f'Channel ID: {channel_id}')



    # Wait for callee to answer

    time.sleep(10) # You need to wait for call to be answered, 10s here is a fixed duration (t=1, t++ loop needed until quit)

    channelResponse2 = requests.get(channelUrl, verify=False)

    channel2 = channelResponse2.json()

    print(f'channel: {channel2}')

    answered = channel2['data'][0]['members'][1]['outbound']['member_status'] # 'outbound' will be 'extension' for internal calls



    # Transfer call to Queue (to first available agent, if no agents are available music on hold will be played)

    if answered == 'ANSWER':

        transferUrl = f'{address}/openapi/v1.0/call/transfer?access_token={access_token}'

        transfer = {
            "type": "blind",
            "channel_id": f"{channel_id}",
            "number": f"{queue}",
            "dial_permission": f"{dialer}"
        }

        transferResponse = requests.post(transferUrl, json = transfer, verify=False)



    # Hang up if no answer

    else:

        print('There is no answer.')

        endUrl = f'{address}/openapi/v1.0/call/hangup?access_token={access_token}'

        end = {
                "channel_id": f"{channel_id}"
        }

        endResponse = requests.post(endUrl, json = end, verify=False)

        print('Call ended.')