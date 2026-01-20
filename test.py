import logging.config

# Setup logging to see the actual request being sent
logging.config.dictConfig({
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '%(name)s: %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'zeep.transports': {
            'level': 'DEBUG',
            'propagate': True,
            'handlers': ['console'],
        },
    }
})

from zeep import Client
from zeep.transports import Transport
import requests
import os
from requests.adapters import HTTPAdapter

# Use local WSDL file to avoid 502 errors when fetching schema from EC servers
wsdl_url = os.path.abspath('goods.wsdl')

# Custom adapter to ensure we use HTTP/1.1 (requests defaults to it, but this is explicit)
class HTTP11Adapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        kwargs['host'] = 'ec.europa.eu'
        return super(HTTP11Adapter, self).init_poolmanager(*args, **kwargs)

# Using a custom session with a User-Agent and forcing HTTP/1.1
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/xml, multipart/related, text/html, image/gif, image/jpeg, *; q=.2, */*; q=.2',
    'Connection': 'keep-alive',
    'Host': 'ec.europa.eu'
})

class LoggingTransport(Transport):
    def post(self, address, message, headers):
        # Force the exact Content-Type that worked in the manual request
        headers['Content-Type'] = 'text/xml;charset=UTF-8'
        
        message_str = message.decode('utf-8') if isinstance(message, bytes) else message
        
        # Manually fix the XML to match the successful pattern
        # 1. Ensure namespaces are at the top and consistent
        # 2. Add empty header if missing
        # 3. Use double quotes
        
        if '<ns0:goodsDescrForWs' in message_str:
            message_str = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" 
                  xmlns:tns="http://goodsNomenclatureForWS.ws.taric.dds.s/">
   <soapenv:Header/>
   <soapenv:Body>
      <tns:goodsDescrForWs>
         <tns:goodsCode>3401201000</tns:goodsCode>
         <tns:languageCode>en</tns:languageCode>
      </tns:goodsDescrForWs>
   </soapenv:Body>
</soapenv:Envelope>"""
        
        message = message_str.encode('utf-8')

        print("\n--- Outgoing Headers ---")
        for k, v in headers.items():
            print(f"{k}: {v}")
        return super().post(address, message, headers)

transport = LoggingTransport(session=session)
client = Client(wsdl=wsdl_url, transport=transport)

# show available operations
print(client.service)

# example call to goodsDescrForWs
# use a real goodsCode and languageCode ('en' lowercase as per schema pattern [a-z][a-z])
response = client.service.goodsDescrForWs(
    goodsCode='3401201000',
    languageCode='en'
)

print(response)

# example call to goodsMeasForWs
response2 = client.service.goodsMeasForWs(
    goodsCode='3401201000',
    countryCode='CN',  # e.g. country of origin
    referenceDate='2026-01-01',
    tradeMovement='I'   # I = import or E = export
)

print(response2)
