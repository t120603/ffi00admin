#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct  7 15:08:28 2021
modules for retrieving necessary information in pixsee clouds
@author: jiakwan2
"""

import requests
import json
import base64
import pytz
from datetime import datetime

### admin apis and top layer api
def queryAdminBaseURL(sku):
    baseurl = ''
    headers = ''

    where = sku.lower()
    if where == 'cn':    ## PIXM02
        headers = {'Authorization':'Bearer MmUzOTY4NGYtZTVhYy00NzM3LWIyNzktYzU3OTQxMDg4MTUz'}
        baseurl = 'https://api.pixseecare.com.cn/api/v1/admin'
    elif where == 'us':  ## PIXM01-US
        headers = {'Authorization':'Bearer HOaz3B6fozO95JT5h0A3RoYnRZfH0KimmNtY'}
        baseurl = 'https://api.ipg-services.com/api/v1/admin'
    elif where == 'tw':  ## PIXM01-TW
        headers = {'Authorization':'Bearer HOaz3B6fozO95JT5h0A3RoYnRZfH0KimmNtY'}
        baseurl = 'https://api.ipg-services.com/api/v1/admin'
    elif where == 'staging':    ## Staging
        headers = {'Authorization':'Bearer HOaz3B6fozO95JT5h0A3RoYnRZfH0KimmNtY'}
        baseurl = 'https://staging.ipg-services.com/api/v1/admin'
    return baseurl, headers

def queryAPIsBaseURL(sku):
    where = sku.lower()
    if where == 'cn':    ## pixm02
        pixseeURL = "https://api.pixseecare.com.cn/api/v1"
    elif where == 'us':  ## pixm0-US
        pixseeURL = "https://api.ipg-services.com/api/v1"
    elif where == 'tw':  ## pixm01-TW
        pixseeURL = "https://api.ipg-services.com/api/v1"
    else:   ## staging
        pixseeURL = 'https://staging.ipg-services.com/api/v1'
    return pixseeURL

def queryAdminSecret(sku):
    where = sku.lower()
    if where == 'cn':    ## pixm02
        pixseeURL = "https://api.pixseecare.com.cn/api/v1"
        cid = 'MGJiMWE1YjctMGYxNi00Njg4LWI2OWItYzgxYjAwZTAxN2Vj'
        csecret = 'ODNhNzI2YzEtMTNkNC00OGZlLWIxMzAtODc4YTU5OGE2ODJi'
    elif where == 'us':  ## pixm0-US
        pixseeURL = "https://api.ipg-services.com/api/v1"
        cid = 'NTkwMWFiMDktNWRjMy00MGY5LTkxYzktNzJiZjQ3OGQ5N2My'
        csecret= 'NGM5MDk3MmYtNDJjMS00MjM2LTk5YjQtNjhiM2NiMDY0N2Zk'
    elif where == 'tw':  ## pixm01-TW
        pixseeURL = "https://api.ipg-services.com/api/v1"
        cid = 'NTkwMWFiMDktNWRjMy00MGY5LTkxYzktNzJiZjQ3OGQ5N2My'
        csecret= 'NGM5MDk3MmYtNDJjMS00MjM2LTk5YjQtNjhiM2NiMDY0N2Zk'
    else:   ## staging
        pixseeURL = 'https://staging.ipg-services.com/api/v1'
        cid = 'ODMwYTQzMTItNmNkMi00MTY0LTg5N2QtZDIyOTI1YWNjM2Zj'
        csecret = 'ZGY3ZjkwNDQtYmRkYy00NjNhLWE4NjktNDI4MWI3ZjRkMDQz'

    return cid, csecret

def queryAllGrandcodeBySN(sku, sno):
    allgcode = []
    base_url, admin_auth = queryAdminBaseURL(sku)
    if base_url != '' and admin_auth != '':
        endpoint = base_url+'/some_devices?sn='+sno
        resp = requests.delete(endpoint, headers=admin_auth)
        if resp.status_code == requests.codes.ok:
            jdata = resp.json()
            for ii in range(len(jdata['result'])):
                thisuser = {}
                thisuser['email'] = jdata['result'][ii]['email']
                thisuser['gcode'] = jdata['result'][ii]['code']
                allgcode.append(thisuser)
    return allgcode

def queryUsersWhoAccessPixsee(sku, ts_start):
    eureka = []
    base_url, admin_auth = queryAdminBaseURL(sku)
    if base_url == '' or admin_auth == '':  ## wrong sku
        return eureka
    ## query users who access pixsee clouds from ts_start
    endpoint = base_url+'/new_accounts?sdt='+ts_start
    resp = requests.get(endpoint, headers=admin_auth)
    #print(endpoint)

    if resp.status_code == 200:
        usersFound = resp.json()
        eureka = usersFound['result']['data']
    return eureka

def getGrandcode(sku, who, sno):
    gcode = ''
    base_url, admin_auth = queryAdminBaseURL(sku)
    if base_url == '' or admin_auth == '':  ## something wrong
        return gcode
    ## query all accounts has bound to this serial number
    endpoint = base_url+'/some_devices?sn='+sno
    resp = requests.delete(endpoint, headers=admin_auth)
    if resp.status_code == 200:
        candidates = resp.json()
        for ii in range(len(candidates['result'])):
            if candidates['result'][ii]['email'] == who:
                gcode = candidates['result'][ii]['code']
                break
    return gcode

def getAccessTokenByGode(sku, gcode):
    atoken = ''
    ##base_url, admin_auth = queryAdminBaseURL(sku)
    ##if base_url == '' or admin_auth == '':  ## something wrong
    ##    return gcode
    ## query API URL
    base_url = queryAPIsBaseURL(sku)
    endpoint = base_url+'/authorization/authorize'
    clientid, clientsecret = queryAdminSecret(sku)
    basicAuth = (clientid, clientsecret)
    ## get access token
    body = {'grant_type':'authorization_code','code':gcode}
    resp = requests.post(endpoint, json=body, auth=basicAuth)
    if resp.status_code == 200:
        result = resp.json()
        atoken = result['access_token']
    return atoken

def getSubscriptionCaseID(sku, mm):
    where = sku.lower()
    if where == 'staging':    ## only 1-month for testing in Staging
        caseid = 'MWE4ZmY4MTQtYjUzYS00NjA3LThhM2QtMjAzOTBkMDEzMTE3'
    else:
        if mm == 12:
            caseid = 'PTx3hqZzVAE0QDDytSkwuRDoqQRsokuy'
        elif mm == 6:
            caseid = 'FYBXoWMK804qWXcqjoZLF8W8Lu3u2IKO'
        elif mm == 3:
            caseid = 'ui2gAQShdCvXwoqtqZH8rZecmom3bK85'
        elif mm == 1:
            caseid = 'NGE3MWQxZDAtNTYwOC00YWE2LWJhMTEtNDcxNWZhN2FhYTI2'
        else:
            caseid = ''
    return caseid

def grantFreeSubscriptionPlan(sku, babyid, caseid, murderer):
    base_url, admin_auth = queryAdminBaseURL(sku)
    admin_auth['Content-Type'] = 'application/x-www-form-urlencoded'
    endpoint = base_url+'/free_purchases'
    payload = 'babyId='+babyid+'&caseId='+caseid+'&payload='+murderer+'-'+str(datetime.now().date())
    
    rtn = requests.post(endpoint, headers=admin_auth, data=payload)
    #resp = rtn.json()
    #print(resp)
    return rtn.status_code

def queryPurchaseStatus(sku, thismail):
    iapstatus = []
    base_url, admin_auth = queryAdminBaseURL(sku)
    endpoint = base_url+'/free_purchases?account='+thismail
    rtn = requests.get(endpoint, headers=admin_auth)
    if rtn.status_code == requests.codes.ok:
        resp = rtn.json()
        for ii in range(len(resp['result'])):
            purchases = {
                'store': resp['result'][ii]['store'],
                'stime': str(datetime.fromtimestamp(resp['result'][ii]['startTime']//1000)),
                'etime': str(datetime.fromtimestamp(resp['result'][ii]['endTime']//1000)),
            }
            iapstatus.append(purchases)
    return iapstatus

def updateActivatedDate(sku, sno, newts):
    base_url, admin_auth = queryAdminBaseURL(sku)
    endpoint = base_url+'/some_devices'
    payload = {'sn':sno, 'activeAt':newts}
    rtn = requests.patch(endpoint, headers=admin_auth, json=payload)
    if rtn.status_code == requests.codes.ok:
        resp = rtn.json()
    else:
        resp = ''
    return resp

def enrollUID(sku, ulist):
    base_url, admin_auth = queryAdminBaseURL(sku)
    endpoint = base_url+'/some_uids'
    payload = {'uids': ulist}
    rtn = requests.post(endpoint, headers=admin_auth, json=payload)
    resp = rtn.json()
    return resp

def enrollDevSN(sku, snlist):
    model = sku.lower()
    if model == 'tw' or model == 'us':
        mname = 'PIXM01'
    elif model == 'cn':
        mname = 'PIXM02'
    else:
        mname = 'STAGING'
    base_url, admin_auth = queryAdminBaseURL(sku)
    endpoint = base_url+'/some_devices'
    payload = {'deviceModel': mname, 'deviceNmae': 'PIXSEE', 'serialNums': snlist}
    rtn = requests.post(endpoint, headers=admin_auth, json=payload)
    resp = rtn.json()
    return resp

### pixsee cloud
def getRecentBoundAccounts(sku):
    # 'recent' means 48-hour ago
    nowdt = datetime.now()
    nzero = datetime(nowdt.year, nowdt.month, nowdt.day, 8)
    sts = int(nzero.timestamp())*1000-48*3600000
    ## query URL, admin token
    recentboundusers = queryUsersWhoAccessPixsee(sku, str(sts))
    return recentboundusers

def checkTimezoneString(tzstr):
    ## correct timezone issue
    if tzstr == 'Asia/Beijing':
        curtz = 'Asia/Shanghai'
    elif tzstr == 'en-US':
        curtz = 'Asia/Taipei'
    else:
        curtz = tzstr
    return curtz

def getAccountDeviceStatus(sku, gcode):
    ## get access token
    atoken = getAccessTokenByGode(sku, gcode)
    ## get account information
    myAA, myBB, myDD, myVV = getAccountDeviceStatusByToken(sku, atoken)
    return myAA, myBB, myDD, myVV

def getAccountDeviceStatusByToken(sku, atoken):
    accountinfo = {}
    infantinfo = []
    deviceinfo = []
    inappinfo = []
    ## get account information
    base_url = queryAPIsBaseURL(sku)
    endpoint = base_url+'/accounts/limit_info'
    auth_header = {'Authorization':'Bearer '+atoken}
    ## get access token
    resp = requests.get(endpoint, headers=auth_header)
    if resp.status_code != 200:
        ## something wrong
        return accountinfo, infantinfo, deviceinfo, inappinfo
    info = resp.json()
    myname = info['result']['name']
    openid = info['result']['openId']
    mymail = info['result']['email']
    shared = info['result']['isVirtualAccount']
    wechat = info['result']['weChatSSO']
    applid = info['result']['appleSSO']
    enroll = info['result']['registerSource']
    ## account information
    accountinfo['myname'] = myname
    accountinfo['atoken'] = atoken
    accountinfo['openid'] = openid
    accountinfo['mymail'] = mymail
    accountinfo['shared'] = shared
    accountinfo['wechat'] = wechat
    accountinfo['applid'] = applid
    accountinfo['enroll'] = enroll
    ## get baby id
    endpoint = base_url+'/babies?openid='+openid
    resp = requests.get(endpoint, headers=auth_header)
    if resp.status_code != 200:
        # something wrong
        return accountinfo, infantinfo, deviceinfo, inappinfo
    baby = resp.json()
    for ii in range(len(baby['result'])):
        thisbaby = {}
        thisbaby['babyid'] = baby['result'][ii]['babyId']
        thisbaby['inappp'] = baby['result'][ii]['subscribed']
        thisbaby['nation'] = baby['result'][ii]['nation']
        thisbaby['shared'] = baby['result'][ii]['inviterName']
        infantinfo.append(thisbaby)
    ## get device information
    for jj in range(len(infantinfo)):
        babyid = infantinfo[jj]['babyid']
        endpoint = base_url+'/devices?babyid='+babyid
        resp = requests.get(endpoint, headers=auth_header)
        if resp.status_code == 200:
            curdev = resp.json()
            for kk in range(len(curdev['result'])):
                thisdevice = {}
                thisdevice['babyid'] = babyid
                thisdevice['devid'] = curdev['result'][kk]['deviceId']
                thisdevice['tutkid'] = curdev['result'][kk]['uid']
                thisdevice['serial'] = curdev['result'][kk]['sn']
                thisdevice['swver'] = curdev['result'][kk]['swVersion']
                thisdevice['hwver'] = curdev['result'][kk]['hwVersion']
                thisdevice['aiver'] = curdev['result'][kk]['aiVersion']
                thisdevice['place'] = curdev['result'][kk]['locationName']
                thisdevice['tzone'] = curdev['result'][kk]['timezone']
                thisdevice['model'] = curdev['result'][kk]['deviceModel']
                thisdevice['dname'] = curdev['result'][kk]['deviceName']
                thisdevice['iotkey'] = curdev['result'][kk]['iotKey']
                #curtz = checkTimezoneString(curdev['result'][kk]['timezone'])
                #thisdevice['bdate'] = datetime.fromtimestamp(curdev['result'][kk]['activeAt']//1000, pytz.timezone(curtz))
                thisdevice['bdate'] = curdev['result'][kk]['activeAt']//1000
                deviceinfo.append(thisdevice)
        #print(deviceinfo[0]['tzone'])
        ### get subscription status
        endpoint = base_url+'/purchases/o?babyid='+babyid
        resp = requests.get(endpoint, headers=auth_header)
        if resp.status_code == 200:
            iap = resp.json()
            for kk in range(len(iap['result'])):
                subscribed = {}
                #thistzone = checkTimezoneString(deviceinfo[0]['tzone'])     ## current: one baby has only one device
                subscribed['store'] = iap['result'][kk]['store']
                #subscribed['start'] = datetime.fromtimestamp(iap['result'][kk]['startTime']//1000, pytz.timezone(thistzone))
                #if iap['result'][kk]['endTime'] == -1:
                #    subscribed['until'] = "(-1: no expiration record)"
                #else:
                #    subscribed['until'] = datetime.fromtimestamp(iap['result'][kk]['endTime']//1000, pytz.timezone(thistzone))
                subscribed['start'] = iap['result'][kk]['startTime']//1000
                subscribed['until'] = iap['result'][kk]['endTime']//1000
                inappinfo.append(subscribed)
    return accountinfo, infantinfo, deviceinfo, inappinfo

def retrieveDevPhotos(sku, atoken, babyid, sts):
    photolist = []
    #fnamelist = []
    lastsync = sts
    errmsg = ''

    base_url = queryAPIsBaseURL(sku)
    param = {"sdt": str(sts*1000)}
    endpoint = base_url+'/storages/s/'+babyid
    auth_header = {'Authorization':'Bearer '+atoken}
    resp = requests.get(endpoint, params=param, headers=auth_header)
    if resp.status_code != 200:
        return lastsync, errmsg, photolist
    photorecord = resp.json()
    if photorecord['code'] != 0:      ## something wrong
        lastsync = int(photorecord['result']['latestSync']//1000)
        errmsg = photorecord['result']['message']
        return lastsync, errmsg, photolist
    #print(atoken)
    #print(babyid)
    #print(photorecord)
    #print(resp.text)
    for ii in range(len(photorecord['result']['data'])):
        photo = {}
        photo['fileid'] = photorecord['result']['data'][ii]['fid']
        photo['shottime'] = photorecord['result']['data'][ii]['photoDateTime']
        photo['updateAt'] = photorecord['result']['data'][ii]['updatedAt']
        photo['thumbnail'] = photorecord['result']['data'][ii]['thumbnail']
        photolist.append(photo)
        #photolist.append(photorecord['result']['data'][ii]['fid'])
        #fnamelist.append(photorecord['result']['data'][ii]['fileName'])

    return lastsync, errmsg, photolist

def retrieveJPEGbyFid(sku, atoken, fid):
    jpgdata = ''
    errmsg = ''

    base_url = queryAPIsBaseURL(sku)
    endpoint = base_url+'/storages/o/'+fid+'?type=1'
    auth_header = {'Authorization':'Bearer '+atoken}
    resp = requests.get(endpoint, headers=auth_header)
    if resp.status_code != requests.codes.ok:
        errmsg = 'Something wrong, can not retrieve JPEG by fid ('+fid+')\ntoken is ('+atoken+')'
    else:
        jpgdata = resp.content
    return errmsg, jpgdata

def retrieveEventHistory(sku, atoken, babyid, sdt, edt, evttype):
    base_url = queryAPIsBaseURL(sku)
    endpoint = base_url+'/event_histories?babyid='+babyid+'&sdt='+str(sdt)+'&edt='+str(edt)+'&ct='+evttype
    auth_header = {'Authorization':'Bearer '+atoken}
    r = requests.get(endpoint, headers=auth_header)
    eventlist = []
    if r.status_code != requests.codes.ok:
        resp = json.loads(r.text)
        for ii in range(len(resp['result'])):
            if resp['result'][ii]['category'] == 'e' or resp['result'][ii]['category'] == 'c':
                thisevent = {}
                thisevent['eid'] = resp['result'][ii]['eid']
                thisevent['type'] = resp['result'][ii]['category']
                thisevent['time'] = resp['result'][ii]['eventTime']
                thisevent['msg'] = resp['result'][ii]['eventMessage']
                eventlist.append(thisevent)
    return eventlist

def removeEvent(sku, atoken, eid):
    base_url = queryAPIsBaseURL(sku)
    endpoint = base_url+'/event_histories/o/'+eid
    auth_header = {'Authorization':'Bearer '+atoken}
    resp = requests.get(endpoint, headers=auth_header)
    jdata = json.loads(resp.text)
    return jdata['message']

def removeDeviceBinding(sku, atoken, devid):
    base_url = queryAPIsBaseURL(sku)
    endpoint = base_url+'/devices/'+devid
    auth_header = {'Authorization':'Bearer '+atoken}
    r = requests.delete(endpoint, headers=auth_header)
    if r.status_code == requests.codes.ok:
        errcode = 0
    else:
        errcode = -1
    return errcode

### vsaas cloud
def queryVsaasURL(sku):
    where = sku.lower()
    if where == 'cn':    ## PIXM02
        vsaasURL = "https://cn-vsaasapi-tutk.kalay.net.cn"
    elif where == 'us':
        vsaasURL = "https://asia-vsaasapi-tutk.kalayservice.com"
    elif where == 'tw':  ## PIXM01-TW
        vsaasURL = "https://asia-vsaasapi-tutk.kalayservice.com"
    else:   # staging
        vsaasURL = 'https://asia-vpapi-tutk-stg.kalay.us'
    return vsaasURL

def queryVsaasRealmSecret(sku):
    where = sku.lower()
    if where == 'cn':    ## PIXM02
        cid = 'Y2YyZWQxZmItZTEyNC00NDMwLWFkZjYtZjlkNGNjMDUyNjM1'
        csecret = 'ODYxMzhkYWEtMmIyZS00ZDRmLWIxOTUtNDRjNzgwNTdiZjI4'
        realm = 'BIOSLAB-cn'
    elif where == 'us':  ## PIXM01-US
        cid = 'NzdlYjlmODMtMzFlNi00M2E5LWIxMzItMmVhMTg2NDgyZjFj'
        csecret = 'OWJlYWRjNmEtZTA2MS00NjJjLWI3ZDMtN2UyN2Y1ZTdlYWQ4'
        realm = 'BIOSLAB'
    elif where == 'tw':  ## PIXM01-TW
        cid = 'NzdlYjlmODMtMzFlNi00M2E5LWIxMzItMmVhMTg2NDgyZjFj'
        csecret = 'OWJlYWRjNmEtZTA2MS00NjJjLWI3ZDMtN2UyN2Y1ZTdlYWQ4'
        realm = 'BIOSLAB'
    else:   # staging
        cid = 'MDIyMmVjNDYtMDU0Zi00OTU1LWJkZmQtNzFmN2JiYTgxMDc4'
        csecret = 'ZmE0M2M5NDktNWRhNC00ZGM1LTk1ZTktZDlmM2ZjZDkzYzhl'
        realm = 'BIOSLAB-stg'
    return cid, csecret, realm

def getAccountVsaasStatus(sku, gcode):
    vsaastoken = ''
    devicelist = []
    contractpk = []
    ## get VSaaS URL and id/secret for querying vsaas token
    baseurl = queryVsaasURL(sku)
    cid, csecret, realm = queryVsaasRealmSecret(sku)
    endpoint = baseurl+'/vsaas/api/v1/auth/oauth_token?realm='+realm
    basicAuth = (cid, csecret)
    body = {'grant_type':'authorization_code','code':gcode}
    resp = requests.post(endpoint, json=body, auth=basicAuth)
    if resp.status_code == 200:
        token = resp.json()
        vsaastoken = token['access_token']
        ## query vsaas contract information
        contractpk = getVsaasContractInfo(sku, vsaastoken)
        devicelist = getVsaasDeviceList(sku, vsaastoken)
    return vsaastoken, contractpk, devicelist

def getVsaasContractInfo(sku, vtoken):
    cinfo = []
    baseurl = queryVsaasURL(sku)
    payload = "query {get_contract_list{pk,account,duration_type,state,created,updated,expires,nickname,description,devices{udid},max_storage_size,storage_usage,max_download_limit,device_bound,max_bound_device}}"
    header = {'Authorization':'Bearer '+vtoken}
    endpoint = baseurl+'/vsaas/api/v1/be'
    r = requests.request("POST", endpoint, headers=header, data=payload)
    if r.status_code == 200:
        resp = json.loads(r.text)
        clist = resp['data']['get_contract_list']
        for ii in range(len(clist)):
            cdict = {}
            cdict['state'] = clist[ii]['state']
            cdict['created'] = vsaasTimeString2TimeStamp(clist[ii]['created'])
            cdict['expired'] = vsaasTimeString2TimeStamp(clist[ii]['expires'])
            cdict['quantity'] = clist[ii]['max_storage_size']
            cdict['usage'] = clist[ii]['storage_usage']
            cdict['maxbound'] = clist[ii]['max_bound_device']
            cdict['nowbound'] = clist[ii]['device_bound']
            cdict['pk'] = clist[ii]['pk']
            ## multiple device, if any
            uidlist = []
            for jj in range(len(clist[ii]['devices'])):
                thisuid = clist[ii]['devices'][jj]['udid']
                uidlist.append(thisuid)
            cdict['udid'] = uidlist
            cinfo.append(cdict)
    return cinfo

def getVsaasDeviceList(sku, vtoken):
    devlist = []
    baseurl = queryVsaasURL(sku)
    payload = "query {get_device_list {vendor,created,updated,account,udid,thumbnail,channel,color_tag,nickname,st,uid,credential, fw_ver}}"
    header = {'Authorization':'Bearer '+vtoken}
    endpoint = baseurl+'/vsaas/api/v1/be'
    r = requests.request("POST", endpoint, headers=header, data=payload)
    if r.status_code == 200:
        resp = json.loads(r.text)
        dlist = resp['data']['get_device_list']
        for ii in range(len(dlist)):
            ddata = {}
            ddata['created'] = vsaasTimeString2TimeStamp(dlist[ii]['created'])
            ddata['fwver'] = dlist[ii]['fw_ver']
            ddata['uid'] = dlist[ii]['uid']
            ddata['updated'] = vsaasTimeString2TimeStamp(dlist[ii]['updated'])
            bstr = base64.b64decode(dlist[ii]['credential'])
            cstr = str(bstr, "utf-8")
            credential = json.loads(cstr)
            ddata['av'] = credential['av']
            ddata['ak'] = credential['ak']
            ddata['identity'] = credential['identity']
            devlist.append(ddata)
    return devlist

def vsaasTimeString2TimeStamp(vsaasstr):
    nt = datetime.strptime(vsaasstr, '%Y-%m-%dT%H:%M:%S.%fZ')
    dtstr = datetime(nt.year, nt.month, nt.day, nt.hour, nt.minute, nt.second)
    ts = int(dtstr.timestamp())
    return ts

def getVsaasEventList(sku, vtoken, uid, sdt, edt):
    baseurl = queryVsaasURL(sku)
    payload = 'query {get_event_list (device:\"'+uid+'\",start_time:\"'+str(int(sdt))+'\",end_time:\"'+str(int(edt))+'\" ,is_archieve:false){pk,created,updated,account,device,start_time,start_time_ts,thumbnail,event_type,is_archieve,expires,url}}'
    header = {'Authorization':'Bearer '+vtoken}
    endpoint = baseurl+'/vsaas/api/v1/be'
    r = requests.request("POST", endpoint, headers=header, data=payload)
    resp = json.loads(r.text)
    evtlist = resp['data']['get_event_list']
    return evtlist

def getVsaasBindingServer(sku, vtoken, thisuid):
    baseurl = queryVsaasURL(sku)
    payload = 'query {get_binding_server (udid:\"'+thisuid+'\")}'
    header = {'Authorization':'Bearer '+vtoken}
    endpoint = baseurl+'/vsaas/api/v1/be'
    r = requests.request("POST", endpoint, headers=header, data=payload)
    resp = json.loads(r.text)
    return resp['data']['get_binding_server']

def removeVsaasEvent(sku, vtoken, pk):
    baseurl = queryVsaasURL(sku)
    payload = 'mutation {remove_event(pk:\"'+pk+'\")}'
    header = {'Authorization':'Bearer '+vtoken}
    endpoint = baseurl+'/vsaas/api/v1/be'
    r = requests.request("POST", endpoint, headers=header, data=payload)
    resp = json.loads(r.text)
    return resp['data']['remove_event']

def removeVsaasBinding(sku, vtoken, uid):
    baseurl = queryVsaasURL(sku)
    payload = 'mutation {remove_binding(device:"'+uid+'")}'
    header = {'Authorization':'Bearer '+vtoken}
    endpoint = baseurl+'/vsaas/api/v1/be'
    r = requests.request("POST", endpoint, headers=header, data=payload)
    r = requests.request("POST", endpoint, headers=header, data=payload)
    if r.status_code == requests.codes.ok:
        removeBinding = 1
    else:
        removeBinding = 0
    ## remove device
    payload = 'mutation {remove_device(udid:"'+uid+'")}'
    r = requests.request("POST", endpoint, headers=header, data=payload)
    #resp = json.loads(r.text)
    if r.status_code == requests.codes.ok:
        removeDevice = 1
    else:
        removeDevice = 0
    return removeBinding, removeDevice

