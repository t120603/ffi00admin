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
        cid = 'MGJiMWE1YjctMGYxNi00Njg4LWI2OWItYzgxYjAwZTAxN2Vj'
        csecret = 'ODNhNzI2YzEtMTNkNC00OGZlLWIxMzAtODc4YTU5OGE2ODJi'
    elif where == 'us':  ## pixm0-US
        cid = 'NTkwMWFiMDktNWRjMy00MGY5LTkxYzktNzJiZjQ3OGQ5N2My'
        csecret = 'NGM5MDk3MmYtNDJjMS00MjM2LTk5YjQtNjhiM2NiMDY0N2Zk'
    elif where == 'tw':  ## pixm01-TW
        cid = 'NTkwMWFiMDktNWRjMy00MGY5LTkxYzktNzJiZjQ3OGQ5N2My'
        csecret = 'NGM5MDk3MmYtNDJjMS00MjM2LTk5YjQtNjhiM2NiMDY0N2Zk'
    else:   ## staging
        cid = 'ODMwYTQzMTItNmNkMi00MTY0LTg5N2QtZDIyOTI1YWNjM2Zj'
        csecret = 'ZGY3ZjkwNDQtYmRkYy00NjNhLWE4NjktNDI4MWI3ZjRkMDQz'
    return cid, csecret

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

def getGrantcode(sku, who, sno):
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
    base_url, admin_auth = queryAdminBaseURL(sku)
    if base_url == '' or admin_auth == '':  ## something wrong
        return gcode
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
    accountinfo = {}
    infantinfo = []
    deviceinfo = []
    inappinfo = []
    ## get access token
    atoken = getAccessTokenByGode(sku, gcode)
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
                curtz = checkTimezoneString(curdev['result'][kk]['timezone'])
                thisdevice['bdate'] = datetime.fromtimestamp(curdev['result'][kk]['activeAt']//1000, pytz.timezone(curtz))
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

def queryAccountDeviceStatus(sku, atoken):
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
                curtz = checkTimezoneString(curdev['result'][kk]['timezone'])
                thisdevice['bdate'] = datetime.fromtimestamp(curdev['result'][kk]['activeAt']//1000, pytz.timezone(curtz))
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
            if ddata['uid'] != '':
                bstr = base64.b64decode(dlist[ii]['credential'])
                ## debug
                #print('({})'.format(ii+1))
                #print(ddata)
                #print(bstr)
                cstr = str(bstr, "utf-8")
                ## debug
                #print('b64decode->unicode is '+cstr)
                credential = json.loads(cstr)
                ddata['av'] = credential['av']
                ddata['ak'] = credential['ak']
                ddata['identity'] = credential['identity']
            else:
                ddata['av'] = ''
                ddata['ak'] = ''
                ddata['identity'] = ''
            devlist.append(ddata)
    return devlist

def vsaasTimeString2TimeStamp(vsaasstr):
    which = '.' in vsaasstr
    if which == True:
        format_string = "%Y-%m-%dT%H:%M:%S.%fZ"
    else:
        format_string = "%Y-%m-%dT%H:%M:%SZ"
    nt = datetime.strptime(vsaasstr, format_string)
    #nt = datetime.strptime(vsaasstr, '%Y-%m-%dT%H:%M:%S.%fZ')
    dtstr = datetime(nt.year, nt.month, nt.day, nt.hour, nt.minute, nt.second)
    ts = int(dtstr.timestamp())
    return ts
