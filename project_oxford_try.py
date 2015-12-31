"""
import http.client, urllib.request, urllib.parse, urllib.error, base64	


headers = {
    # Request headers
    'Ocp-Apim-Subscription-Key': '3e1001fe09914ef184e5bcd79aa74d2a',
}

params = urllib.parse.urlencode({
    # Request parameters
    'model': 'body',
    #'text': 'suck your tits',
    #'order': '5',
    #'maxNumOfCandidatesReturned': '1',
})

try:
    conn = http.client.HTTPSConnection('api.projectoxford.ai')
    conn.request("POST", "/text/weblm/v1.0/calculateJointProbability?%s" % params, "give up the man inside", headers)
    response = conn.getresponse()
    data = response.read()
    print(data)
    conn.close()
except Exception as e:
    print("[Errno {0}] {1}".format(e.errno, e.strerror))



"""


 #urllib.parse, urllib.error


"""
try:
    conn = http.client.HTTPSConnection('api.projectoxford.ai')
    conn.request("POST", "/text/weblm/v1.0/calculateJointProbability?%s" % params, "{\"queries\": [\"this\",\"is\",\"this is\"]}", headers)
    print(conn.getresponse().read())
    conn.close()
except Exception as e:
    print("[Errno {0}] {1}".format(e.errno, e.strerror))
"""
####################################
import json
"""
res = b'{"results":[{"words":"input","probability":-4.16},{"words":"input to","probability":-5.83},{"words":"been inputting","probability":-9.338},{"words":"been inputting to","probability":-11.445}]}'

a = json.loads(res.decode('utf-8'))['results']

print(float(a[0]['probability']))"""

a = dict()
a['queries'] = []
a['queries'].append(1)
a['queries'].append(2)
a['queries'].append(4)
a['queries'].append(1)
print(a)