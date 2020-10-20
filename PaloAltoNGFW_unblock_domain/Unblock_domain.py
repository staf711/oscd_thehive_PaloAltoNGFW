#!/usr/bin/env python3
# encoding: utf-8

from cortexutils.responder import Responder
from thehive4py.api import TheHiveApi
from panos import firewall
import panos.objects

class Download_log(Responder):
    def __init__(self):
        Responder.__init__(self)
        self.hostname_PaloAltoNGFW = self.get_param('config.Hostname_PaloAltoNGFW')
        self.User_PaloAltoNGFW = self.get_param('config.User_PaloAltoNGFW')
        self.Password_PaloAltoNGFW = self.get_param('config.Password_PaloAltoNGFW')
        self.name_internal_Address_Group_for_domain = self.get_param('config.name_internal_Address_Group_for_domain')
        self.thehive_instance = self.get_param('config.thehive_instance')
        self.thehive_api_key = self.get_param('config.thehive_api_key', 'YOUR_KEY_HERE')
        self.api = TheHiveApi(self.thehive_instance, self.thehive_api_key)

    def run(self):
        alertId = self.get_param('data.id')
        response = self.api.get_alert(alertId)
        ioc=None
        ioc_clear=[]
        for i in list(response.json().get("artifacts")):
            if 'hostname' in str(i):
                ioc = i.get("data")
                for i in ioc:
                    if i == "[" or i == "]":
                        continue
                    else:
                        ioc_clear.append(i)
                ioc="".join(ioc_clear)
        fw = firewall.Firewall(self.hostname_PaloAltoNGFW, api_username=self.User_PaloAltoNGFW, api_password=self.Password_PaloAltoNGFW)
        panos.objects.AddressGroup.refreshall(fw)
        block_list = fw.find(self.name_external_Address_Group, panos.objects.AddressGroup)
        ioc_list = block_list.about().get('static_value')
        if ioc in ioc_list:
            ioc_list.remove(ioc)
            temp1 = panos.objects.AddressGroup(name_internal_Address_Group_for_domain, static_value=ioc_list)
            fw.add(temp1)
            temp1.apply()
        
        
        panos.objects.AddressObject.refreshall(fw)
        if ioc in str(fw.find(ioc, panos.objects.AddressObject)):
            deleted_ioc = fw.find(ioc, panos.objects.AddressObject)
            deleted_ioc.delete()
        
        self.report({'message': 'message sent'})

if __name__ == '__main__':
    Download_log().run()
