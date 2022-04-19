import requests
import json
from datetime import datetime
import pytz
import base64
import getpass

global allusers_staging, allusers_pixm01, allusers_pixm02
global lenStagingUsers, lenPixm01Users, lenPixm02Users
global cur_tz
global lastOption

def topMenu():
    print('\n+------------------------------------------------+')
    print('|   1) check information by account              |')
    print('|   2) check information by serial number        |')
    print('|   0) bye bye                                   |')
    print('+------------------------------------------------+')
    try:
        idx = int(input('    Enter your choice: '))
    except ValueError:
        print('\t<Error> Please enter an integer\n\n')
        idx = -1
    return idx

def secondMenu(sns):
    while True:
        print('\n...................................................................')
        print(':   1) continue checking next account/SN                          :')
        print(':   2) check all bound accounts with device ({sn})       :'.format(sn=sns))
        print(':   3) check events in VSaaS within a time interval               :')
        print(':   4) check events (area & cry) in pixsee within a time interval :')
        print(':   5) check photos in pixsee within a time interval              :')
        #print(':   6) delete event from VSaaS server                             :')
        print(':   0) Close this utility                                         :')
        print(':.................................................................:')
        try:
            idx = int(input('    Enter your choice> '))
        except ValueError:
            print('\t<Error> Please enter an integer\n\n')
            idx = -1
        if idx >= 0 and idx <= 6:
            break
        else:
            print('\t<! WARNING !> Please input a number 1~6, try again')

    print('========        ========')
    return idx

def whichSKU():
    global cur_tz

    sku = 0
    while True:
        print('\n+------------------------------------------------+')
        print('|   0) Staging environment                       |')
        print('|   1) PIXM01-TW production environment          |')
        print('|   2) PIXM01-US production environment          |')
        print('|   3) PIXM02(CN) production environment         |')
        print('+------------------------------------------------+')
        try:
            sku = int(input('    Which environment? '))
        except ValueError:
            print("\t[FATAL] Please enter an integer, try it again")

        if sku >= 0 and sku < 3:
            cur_tz = "Asia/Taipei"      ## default timezone
            break
        elif sku == 3:
            cur_tz = "Asia/Shanghai"    ## default timezone
            break
        else:
            print('\t[ERROR] Please enter a (0-3) integer\n\n')
    return sku

def login_by_account():
    thisname = input('   Account: ')
    thispass = getpass.getpass('  Password: ')
    thisaccount = {'account':thisname, 'password':thispass}
    return thisaccount

### timezone issue
def checkTimezone(tz):
    if tz == 'Asia/Beijing':
        curtz = 'Asia/Shanghai'
    elif tz == 'en-US':      ## legacy issue in development/testing
        curtz = 'Asia/Taipei'
    else:
        curtz = tz
    return curtz

### admin apis
def getURLpixsee(sku):
    if sku == 3:    ## pixm02
        pixseeURL = "https://api.pixseecare.com.cn/api/v1"
        cid = 'MGJiMWE1YjctMGYxNi00Njg4LWI2OWItYzgxYjAwZTAxN2Vj'
        csecret = 'ODNhNzI2YzEtMTNkNC00OGZlLWIxMzAtODc4YTU5OGE2ODJi'
    elif sku == 2:  ## pixm0-US
        pixseeURL = "https://api.ipg-services.com/api/v1"
        cid = 'NTkwMWFiMDktNWRjMy00MGY5LTkxYzktNzJiZjQ3OGQ5N2My'
        csecret= 'NGM5MDk3MmYtNDJjMS00MjM2LTk5YjQtNjhiM2NiMDY0N2Zk'
    elif sku == 1:  ## pixm01-TW
        pixseeURL = "https://api.ipg-services.com/api/v1"
        cid = 'NTkwMWFiMDktNWRjMy00MGY5LTkxYzktNzJiZjQ3OGQ5N2My'
        csecret= 'NGM5MDk3MmYtNDJjMS00MjM2LTk5YjQtNjhiM2NiMDY0N2Zk'
    else:   ## staging
        pixseeURL = 'https://staging.ipg-services.com/api/v1'
        cid = 'ODMwYTQzMTItNmNkMi00MTY0LTg5N2QtZDIyOTI1YWNjM2Zj'
        csecret = 'ZGY3ZjkwNDQtYmRkYy00NjNhLWE4NjktNDI4MWI3ZjRkMDQz'

    return pixseeURL, cid, csecret

def getURLadmin(sku):
    if sku == 3:    ## PIXM02
        headers = {'Authorization':'Bearer MmUzOTY4NGYtZTVhYy00NzM3LWIyNzktYzU3OTQxMDg4MTUz'}
        adminURL = 'https://api.pixseecare.com.cn/api/v1/admin'
    elif sku == 2:  ## PIXM01-US
        headers = {'Authorization':'Bearer HOaz3B6fozO95JT5h0A3RoYnRZfH0KimmNtY'}
        adminURL = 'https://api.ipg-services.com/api/v1/admin'
    elif sku == 1:  ## PIXM01-TW
        headers = {'Authorization':'Bearer HOaz3B6fozO95JT5h0A3RoYnRZfH0KimmNtY'}
        adminURL = 'https://api.ipg-services.com/api/v1/admin'
    else:           ## Staging
        headers = {'Authorization':'Bearer HOaz3B6fozO95JT5h0A3RoYnRZfH0KimmNtY'}
        adminURL = 'https://staging.ipg-services.com/api/v1/admin'
    return adminURL, headers

def getURLvsaas(sku):
    if sku == 3:    ## PIXM02
        vsaasURL = "https://cn-vsaasapi-tutk.kalay.net.cn"
        cid = 'Y2YyZWQxZmItZTEyNC00NDMwLWFkZjYtZjlkNGNjMDUyNjM1'
        csecret = 'ODYxMzhkYWEtMmIyZS00ZDRmLWIxOTUtNDRjNzgwNTdiZjI4'
        realm = 'BIOSLAB-cn'
    elif sku == 2:  ## PIXM01-US
        vsaasURL = "https://asia-vsaasapi-tutk.kalayservice.com"
        cid = 'NzdlYjlmODMtMzFlNi00M2E5LWIxMzItMmVhMTg2NDgyZjFj'
        csecret = 'OWJlYWRjNmEtZTA2MS00NjJjLWI3ZDMtN2UyN2Y1ZTdlYWQ4'
        realm = 'BIOSLAB'
    elif sku == 1:  ## PIXM01-TW
        vsaasURL = "https://asia-vsaasapi-tutk.kalayservice.com"
        cid = 'NzdlYjlmODMtMzFlNi00M2E5LWIxMzItMmVhMTg2NDgyZjFj'
        csecret = 'OWJlYWRjNmEtZTA2MS00NjJjLWI3ZDMtN2UyN2Y1ZTdlYWQ4'
        realm = 'BIOSLAB'
    else:   # staging
        vsaasURL = 'https://asia-vpapi-tutk-stg.kalay.us'
        cid = 'MDIyMmVjNDYtMDU0Zi00OTU1LWJkZmQtNzFmN2JiYTgxMDc4'
        csecret = 'ZmE0M2M5NDktNWRhNC00ZGM1LTk1ZTktZDlmM2ZjZDkzYzhl'
        realm = 'BIOSLAB-stg'
    return vsaasURL, cid, csecret, realm

def queryAllAccounts(sku):
    global lenStagingUsers, lenPixm01Users, lenPixm02Users
    global allusers_staging, allusers_pixm01, allusers_pixm02
    #print("len = {0}; {1}; {2}".format(lenPixm01Users, lenPixm02Users, lenStagingUsers))
    if sku == 3:    ## PIXM02
        if lenPixm02Users > 0:
            return -100
    elif sku == 1 or sku == 2:   ## PIXM01
        if lenPixm01Users > 0:
            return -100
    else:    ## Staging
        if lenStagingUsers > 0:
            return -100
    baseurl, auth_header = getURLadmin(sku)
    ## search all records since 2020-07-01
    endpoint = baseurl+'/new_accounts?sdt=1593532800000'
    rtn = requests.get(endpoint, headers=auth_header)
    resp = rtn.json()
    if rtn.status_code == 200:
        if sku == 3:    ## PIXM02
            allusers_pixm02 = resp['result']['data']
            lenPixm02Users = len(allusers_pixm02)
        elif sku == 1 or sku ==2:   ## PIXM01
            allusers_pixm01 = resp['result']['data']
            lenPixm01Users = len(allusers_pixm01)
        else:    ## Staging
            allusers_staging = resp['result']['data']
            lenStagingUsers = len(allusers_staging)
    return 0

def findAccountbySN(sku, snstr):
    global allusers_staging, allusers_pixm01, allusers_pixm02

    eureka = ''
    if len(snstr) != 13:
        return -1, eureka       # ERR_WRONG_SERIAL_NUMBER
    snnum = int(snstr)
    ## check snnum has bound or not
    ####baseurl, auth_header = getURLadmin(sku)
    ## search all records since 2020-07-01
    ####endpoint = baseurl+'/new_accounts?sdt=1593532800000'
    ####rtn = requests.get(endpoint, headers=auth_header)
    ####resp = rtn.json()
    ####if rtn.status_code != 200:
    ####    return -2, eureka       # ERR_NOT_200
    ####allusers = resp['result']['data']
    errcode = queryAllAccounts(sku)
    #if errcode < 0:
    #    return -2, eureka       # ERR_NOT_200
    if sku == 3:    ## PIXM02
        allusers = allusers_pixm02
    elif sku == 1 or sku ==2:   ## PIXM01
        allusers = allusers_pixm01
    else:    ## Staging
        allusers = allusers_staging

    for iii in range(len(allusers)):
        devices = allusers[iii]['devices']
        #print(devices)
        if len(devices) == 0:
            continue
        for kk in range(len(devices)):
            if devices[kk]['serialNumber'] == snstr:
                eureka = allusers[iii]['account']['email']
                break
        if eureka != '':
            break
    if eureka == '':
        return -3, eureka       # ERR_NOT_FOUND
    return 0, eureka

def getAccessToken_pixsee_bygcode(sku, gcode):
    atoken = ''
    ## get pixseeURL
    pixseeURL, clientid, clientsecret = getURLpixsee(sku)
    ## get access Token
    body = {'grant_type':'authorization_code','code':gcode}
    basicAuth = (clientid, clientsecret)
    endpoint = pixseeURL+'/authorization/authorize'
    r = requests.post(endpoint, json=body, auth=basicAuth)
    resp = r.json()
    if r.status_code == 200:
        atoken = resp['access_token']
    else:
        return -6, atoken

    return 0, atoken

def getAccessToken_pixsee_byUA(sku, account):
    gcode = ''
    atoken = ''
    ## get pixseeURL
    pixseeURL, clientid, clientsecret = getURLpixsee(sku)
    ## get grantcode
    endpoint = pixseeURL+'/authorization/login'
    r = requests.request('POST', endpoint, json=account)
    resp = r.json()
    if r.status_code == 200:
        gcode = resp['result']['code']
    else:
        return -11, gcode, atoken
    if gcode == '':
        return -11, gcode, atoken
    ## get access Token
    body = {'grant_type':'authorization_code','code':gcode}
    basicAuth = (clientid, clientsecret)
    endpoint = pixseeURL+'/authorization/authorize'
    r = requests.post(endpoint, json=body, auth=basicAuth)
    resp = r.json()
    if r.status_code == 200:
        atoken = resp['access_token']
    else:
        return -6, gcode, atoken

    return 0, gcode, atoken

def getAllGrantcode_by_sn(sku, snstr):
    allGcode = []
    errcode = 0
    adminurl, auth_header = getURLadmin(sku)
    endpoint = adminurl+'/some_devices?sn='+snstr
    r = requests.delete(endpoint, headers=auth_header)
    if r.status_code != 200:
        return -4, allGcode
    resp = r.json()
    for iii in range(len(resp['result'])):
        thisaccount = {}
        thisaccount['email'] = resp['result'][iii]['email']
        thisaccount['gcode'] = resp['result'][iii]['code']
        allGcode.append(thisaccount)
    if len(allGcode) == 0:
        errcode = -12
    return errcode, allGcode

def getAccessToken_pixsee_bySN(sku, snstr, findme):
    ## adminAPI: get grant code by SN
    accesstoken = ''
    grantcode = ''
    adminurl, auth_header = getURLadmin(sku)
    endpoint = adminurl+'/some_devices?sn='+snstr
    r = requests.delete(endpoint, headers=auth_header)
    if r.status_code != 200:
        return -4, grantcode, accesstoken
    resp = r.json()
    for iii in range(len(resp['result'])):
        if resp['result'][iii]['email'] == findme:
            grantcode = resp['result'][iii]['code']
            break
    if grantcode == '':
        return -5, grantcode, accesstoken
    ## get (pixsee) access token
    baseurl, clientid, clientsecret = getURLpixsee(sku)
    body = {'grant_type':'authorization_code','code':grantcode}
    basicAuth = (clientid, clientsecret)
    endpoint = baseurl+'/authorization/authorize'
    r = requests.post(endpoint, json=body, auth=basicAuth)
    resp = r.json()
    errcode = 0
    if r.status_code == 200:
        accesstoken = resp['access_token']
        if accesstoken == '':
            errcode = -6
    else:
        errcode = -6
    return errcode, grantcode, accesstoken

def getUserDeviceStatus(sku, pixseetoken):
    global cur_tz

    userinfo = {}
    deviceinfo = []
    iapinfo = []
    errcode = 0
    ## get pixseeURL
    pixseeURL, clientid, clientsecret = getURLpixsee(sku)
    auth_header = {'Authorization':'Bearer '+pixseetoken}
    ## get openID
    endpoint = pixseeURL+'/accounts/limit_info'
    r = requests.get(endpoint, headers=auth_header)
    resp = r.json()
    openid = ''
    if r.status_code == 200:
        myname = resp['result']['name']
        openid = resp['result']['openId']
        mymail = resp['result']['email']
        shared = resp['result']['isVirtualAccount']
        wechat = resp['result']['weChatSSO']
        aplsso = resp['result']['appleSSO']
        enroll = resp['result']['registerSource']
    else:
        errcode = -7
    if openid == '':
        errcode = -7
    if errcode != 0:
        return errcode, userinfo, deviceinfo, iapinfo
    ## get babyID
    endpoint = pixseeURL+'/babies?openid='+openid
    r = requests.get(endpoint, headers=auth_header)
    resp = r.json()
    babyid = []
    inviter = []
    if r.status_code == 200:
        for iii in range(len(resp['result'])):
            thisbaby = resp['result'][iii]['babyId']
            babyid.append(thisbaby)
            inviter.append(resp['result'][iii]['inviterName'])
    else:
        errcode = -8
    if len(babyid) == 0:
        errcode = -8
    if errcode != 0:
        return errcode, userinfo, deviceinfo, iapinfo
    ## get device info
    #print(babyid)
    for idx in range(len(babyid)):
        thisbaby = babyid[idx]
        endpoint = pixseeURL+'/devices?babyid='+thisbaby
        r = requests.get(endpoint, headers=auth_header)
        if r.status_code == 200:
            resp = r.json()
            for iii in range(len(resp['result'])):
                thisdevice = {}
                #print(resp['result'][iii])
                thisdevice['babyid'] = thisbaby
                thisdevice['uid'] = resp['result'][iii]['uid']
                thisdevice['sn'] = resp['result'][iii]['sn']
                thisdevice['swver'] = resp['result'][iii]['swVersion']
                thisdevice['hwver'] = resp['result'][iii]['hwVersion']
                thisdevice['aiver'] = resp['result'][iii]['aiVersion']
                thisdevice['tzone'] = resp['result'][iii]['timezone']
                cur_tz = checkTimezone(thisdevice['tzone'])
                thisdevice['deviceid'] = resp['result'][iii]['deviceId']
                thisdevice['loc'] = resp['result'][iii]['locationName']
                thisdevice['model'] = resp['result'][iii]['deviceModel']
                thisdevice['name'] = resp['result'][iii]['deviceName']
                thisdevice['iotKey'] = resp['result'][iii]['iotKey']
                thisdevice['activated'] = datetime.fromtimestamp(resp['result'][iii]['activeAt']//1000, pytz.timezone(cur_tz))
                ### inviterName field came from get_baby_id by openId
                thisdevice['inviter'] = inviter[idx]
                ###
                deviceinfo.append(thisdevice)
        ## get subscription status
        endpoint = pixseeURL+'/purchases/o?babyid='+thisbaby+'&accountid='+openid
        r = requests.get(endpoint, headers=auth_header)
        if r.status_code == 200:
            resp = r.json()
            for iii in range(len(resp['result'])):
                subscribed = {}
                subscribed['store'] = resp['result'][iii]['store']
                subscribed['start'] = datetime.fromtimestamp(resp['result'][iii]['startTime']//1000, pytz.timezone(cur_tz))
                if resp['result'][iii]['endTime'] == -1:
                    subscribed['end'] = "(-1: no expiration record)"
                else:
                    subscribed['end'] = datetime.fromtimestamp(resp['result'][iii]['endTime']//1000, pytz.timezone(cur_tz))
                iapinfo.append(subscribed)

    if len(deviceinfo) == 0:
        return -9, userinfo, deviceinfo, iapinfo

    ## user information (access token, openID, deviceID, babyID)
    userinfo['myname'] = myname
    userinfo['atoken'] = pixseetoken
    userinfo['openid'] = openid
    userinfo['mymail'] = mymail
    userinfo['shared'] = shared
    userinfo['wechat'] = wechat
    userinfo['aplsso'] = aplsso
    userinfo['enroll'] = enroll

    return 0, userinfo, deviceinfo, iapinfo

def getEventHistory(sku, atoken, babyid, sdt, edt, evttype):
    pixseeURL, clientid, clientsecret = getURLpixsee(sku)
    auth_header = {'Authorization':'Bearer '+atoken}
    endpoint = pixseeURL+'/event_histories?babyid='+babyid+'&sdt='+str(sdt)+'&edt='+str(edt)+'&ct='+evttype
    r = requests.get(endpoint, headers=auth_header)
    eventlist = []
    if r.status_code == requests.codes.ok:
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

def deleteEvent_pixsee(sku, atoken, eid):
    pixseeURL, clientid, clientsecret = getURLpixsee(sku)
    auth_header = {'Authorization':'Bearer '+atoken}
    endpoint = pixseeURL+'/event_histories/o/'+eid
    r = requests.delete(endpoint, headers=auth_header)
    #if r.status_code == requests.codes.ok:
    resp = json.loads(r.text)
    retmsg = resp['message']
    return retmsg

def syncPhotos(sku, atoken, babyid, sdt):
    pixseeURL, clientid, clientsecret = getURLpixsee(sku)
    auth_header = {'Authorization':'Bearer '+atoken}
    endpoint = pixseeURL+'/storages/s/'+babyid+'?sdt='+str(sdt)
    r = requests.get(endpoint, headers=auth_header)
    photolist = []
    synctill = 0
    if r.status_code == requests.codes.ok:
        resp = json.loads(r.text)
        synctill = resp['result']['latestSync']
        for ii in range(len(resp['result']['data'])):
            thisphoto = {}
            thisphoto['fid'] = resp['result']['data'][ii]['fid']
            thisphoto['time'] = resp['result']['data'][ii]['photoDateTime']
            thisphoto['update'] = resp['result']['data'][ii]['updatedAt']
            thisphoto['thumbnail'] = resp['result']['data'][ii]['thumbnail']
            photolist.append(thisphoto)
    return synctill, photolist

### VSaaS apis
def getVSaaS_url(sku):
    if sku == 3:    ## PIXM02
        vsaasURL = "https://cn-vsaasapi-tutk.kalay.net.cn"
    elif sku == 2:  ## PIXM01-US
        vsaasURL = "https://asia-vsaasapi-tutk.kalayservice.com"
    elif sku == 1:  ## PIXM01-TW
        vsaasURL = "https://asia-vsaasapi-tutk.kalayservice.com"
    else:   # staging
        vsaasURL = 'https://asia-vpapi-tutk-stg.kalay.us'
    return vsaasURL

def getAccessToken_vsaas(sku, gcode):
    vatoken = ''
    errcode = 0
    vsaasurl, cid, csecret, realm = getURLvsaas(sku)
    body = {'grant_type':'authorization_code','code':gcode}
    basicAuth = (cid, csecret)
    endpoint = vsaasurl+'/vsaas/api/v1/auth/oauth_token?realm='+realm
    r = requests.post(endpoint, json=body, auth=basicAuth)
    resp = r.json()
    if r.status_code == 200:
        vatoken = resp['access_token']
    else:
        errcode = -10

    return errcode, vatoken

def queryContractInfo_vsaas(sku, atoken):
    contractlist = []
    vsaasurl = getVSaaS_url(sku)
    payload = "query {get_contract_list{pk,account,duration_type,state,created,updated,expires,nickname,description,devices{udid},max_storage_size,storage_usage,max_download_limit,device_bound,max_bound_device}}"
    header = {'Authorization':'Bearer '+atoken}
    endpoint = vsaasurl+'/vsaas/api/v1/be'
    r = requests.request("POST", endpoint, headers=header, data=payload)
    resp = json.loads(r.text)
    if r.status_code == 200:
        clist = resp['data']['get_contract_list']
        for idx in range(len(clist)):
            cdict = {}
            cdict['state'] = clist[idx]['state']
            cdict['created'] = clist[idx]['created']
            cdict['expired'] = clist[idx]['expires']
            cdict['quantity'] = clist[idx]['max_storage_size']
            cdict['usage'] = clist[idx]['storage_usage']
            cdict['maxbound'] = clist[idx]['max_bound_device']
            cdict['nowbound'] = clist[idx]['device_bound']
            ## multiple device
            uidlist = []
            for jjj in range(clist[idx]['device_bound']):
                #print(clist[idx]['devices'])
                if len(clist[idx]['devices']) > 0:
                    thisuid = clist[idx]['devices'][jjj]['udid']
                    uidlist.append(thisuid)

            cdict['uids'] = uidlist

            contractlist.append(cdict)
    return contractlist

def queryDeviceList_vsaas(sku, atoken):
    vsaasurl = getVSaaS_url(sku)
    getDeviceList = "query {get_device_list {vendor,created,updated,account,udid,thumbnail,channel,color_tag,nickname,st,uid,credential, fw_ver}}"
    header = {"Authorization":'Bearer '+atoken}
    endpoint = vsaasurl+'/vsaas/api/v1/be'
    r = requests.request("POST", endpoint, headers=header, data = getDeviceList)
    resp = json.loads(r.text)
    #print(resp)
    return resp['data']['get_device_list']

def queryEventList_vsaas(sku, atoken, thisuid, sdt, edt):
    vsaasurl = getVSaaS_url(sku)
    header = {'Authorization':'Bearer '+atoken}
    endpoint = vsaasurl+'/vsaas/api/v1/be'
    getEventList = 'query {get_event_list (device:\"'+thisuid+'\",start_time:\"'+str(int(sdt))+'\",end_time:\"'+str(int(edt))+'\" ,is_archieve:false){pk,created,updated,account,device,start_time,start_time_ts,thumbnail,event_type,is_archieve,expires,url}}'
    r = requests.request("POST", endpoint, headers=header, data=getEventList)
    resp = json.loads(r.text)
    eventlist = resp['data']['get_event_list']
    return eventlist

def getBindingServer_vsaas(sku, atoken, thisuid):
    vsaasurl = getVSaaS_url(sku)
    header = {'Authorization':'Bearer '+atoken}
    endpoint = vsaasurl+'/vsaas/api/v1/be'
    bindServer = 'query {get_binding_server (udid:\"'+thisuid+'\")}'
    r = requests.request("POST", endpoint, headers=header, data=bindServer)
    resp = json.loads(r.text)
    #print(resp['data']['get_binding_server'])
    return resp['data']['get_binding_server']

def getDownloadURL_vsaas(atoken, evurl, thisuid, ts):
    header = {'Authorization':'Bearer '+atoken}
    endpoint = 'https://'+evurl+'/ask'
    m3u8 = 'query {ask_media (device:\"'+thisuid+'\",timestamp:\"'+ts+'\",length:60,mode:ASK_EVENT){code,ret,url}}'
    r = requests.request("POST", endpoint, headers=header, data=m3u8)
    resp = json.loads(r.text)
    if r.status_code == 200:
        m3u8url = resp['data']["ask_media"]["url"]
    else:
        m3u8url = ""
    return m3u8url

def deleteEvent_vsaas(sku, atoken, pk):
    vsaasurl = getVSaaS_url(sku)
    header = {'Authorization':'Bearer '+atoken}
    endpoint = vsaasurl+'/vsaas/api/v1/be'
    delEvent = 'mutation {remove_event(pk:\"'+pk+'\")}'
    r = requests.request("POST", endpoint, headers=headers, data=payload)
    #if r.status_code == 200:
    resp = json.loads(r.text)
    return resp['data']['remove_event']

def showWarningMessage(errcode):
    print('---..---..---..---..---..---..---..---..---..---..---..')
    if errcode == -1:
        print("<WARNING> It is not pixsee's serial number!")
    elif errcode == -2:
        print("<FATAL> Failed to get data from pixsee cloud, try it later")
    elif errcode == -3:
        print("<ERROR> This device (serial number) was not bound to an account")
    elif errcode == -4:
        print("<ERROR> Can't get grant code from pixsee cloud")
    elif errcode == -5:
        print("<WARNING> Account registered, but never bound to any device yet")
    elif errcode == -6:
        print("<ERROR> Can't get user's access token")
    elif errcode == -7:
        print("<ERROR> Can't get user's openID")
    elif errcode == -8:
        print("<ERROR> Can't get user's baby's babyID")
    elif errcode == -9:
        print("<ERROR> This user does not register any baby information to pixsee cloud")
    elif errcode == -10:
        print("<ERROR> unable to get access token from VSaaS")
    elif errcode == -11:
        print("<WARNING> your account or password is wrong, please try again!")
    elif errcode == -12:
        print("<WARNING> This device does not bind to any account in current VSaaS environment")
    else:
        print("Oops!! I can't tell the root cause, please contact with Philip.")
    print('---..---..---..---..---..---..---..---..---..---..---..\n')

## __main__
print('\n+--------------------------------------------------+')
print('  This utility is for querying account information  ')
print('  in pixsee cloud and VSaaS services by device      ')
print('  serial number or account/password')
print('+--------------------------------------------------+')

# initialize parameters
lenStagingUsers = 0
lenPixm01Users = 0
lenPixm02Users = 0
lastOption = 0

while True:
    option = topMenu()
    ## request to input SKU
    if option == 0: ## close this utility
        print('\n**** See you soon! ****\n')
        break
    elif option < 0:
        byebye = False
        continue
    elif option > 2:
        byebye = False
        continue
    sku = whichSKU()

    if option == 2:     ## by serial number
        if lastOption == 1:
            lenStagingUsers = 0
            lenPixm01Users = 0
            lenPixm02Users = 0
        lastOption = 2
            #print("!!!!!!! change to SN !!!!!!")
        ## request to input serail Number
        while True:
            snstr = input("    Please enter device serial number:> " )
            if len(snstr) != 13:
                print('\t[ERROR] Please enter a 13-digit serial number\n\n')
            else:
                print('    --------        --------\n')
                break
        ## query pixsee/VSaaS information by serial Number
        ## find bound account by SN
        errcode, account = findAccountbySN(sku, snstr)
        if errcode < 0:
            showWarningMessage(errcode)
            continue
        #### get access_token from pixsee cloud
        errcode, gcode, atoken_pixsee = getAccessToken_pixsee_bySN(sku, snstr, account)
        if errcode < 0:
            showWarningMessage(errcode)
            continue
    elif option == 1:   ## by account/Password
        if lastOption == 2:
            lenStagingUsers = 0
            lenPixm01Users = 0
            lenPixm02Users = 0
        lastOption = 1
            #print("!!!!!!! change to ACCOUNT !!!!!!")
        me = login_by_account()
        errcode, gcode, atoken_pixsee = getAccessToken_pixsee_byUA(sku, me)
        if errcode < 0:
            showWarningMessage(errcode)
            continue
    else:
        continue

    errcode, uinfo, dinfo, pinfo = getUserDeviceStatus(sku, atoken_pixsee)
    if errcode < 0:
        showWarningMessage(errcode)
        continue
    ## query account informationin VSaaS
    errcode, atoken_vsaas = getAccessToken_vsaas(sku, gcode)
    if errcode < 0:
        showWarningMessage(errcode)
        continue
    uinfo['vatoken'] = atoken_vsaas
    contractlist = queryContractInfo_vsaas(sku, atoken_vsaas)
    devlist = queryDeviceList_vsaas(sku, atoken_vsaas)
    ## print pixsee/VSaaS information
    print("pixsee user '"+uinfo['myname']+"' (email is "+uinfo['mymail']+"):")
    print("\tAccess Token (pixsee):\t"+uinfo['atoken'])
    print("\topen ID (pixsee):\t"+uinfo['openid'])
    #print SSO
    print("\tenrolled at:\t"+uinfo['enroll'])
    if uinfo['shared'] == False:
        print("\tthis account is not a virtual account")
    else:
        print("\tthis account is a virtual account")
    if uinfo['wechat'] == False:
        print("\tthis account did not bound to WeChat(SSO)")
    else:
        print("\tthis account bound to WeChat(SSO)")
    if uinfo['aplsso'] == False:
        print("\tthis account did not bound to AppleID(SSO)")
    else:
        print("\tthis account bound to AppleID(SSO)")
    #print(dinfo)
    for idx in range(len(dinfo)):
        print("  **** {devno} device ({sn}) information ****".format(devno=idx+1, sn=dinfo[idx]['sn']))
        ## v5, check if this babyid was shared by other
        if (dinfo[idx]['inviter'] != ''):
            print("\tthis device is shared by {}".format(dinfo[idx]['inviter']))
            continue
        ###
        print("\tbaby ID is: \t{}".format(dinfo[idx]['babyid']))
        print("\tdevice ID is: \t{}".format(dinfo[idx]['deviceid']))
        #textResult.insert(END, "\tSerial Number is: \t{}\n".format(dinfo[idx]['sn']))
        print("\tdevice UID is: \t{}".format(dinfo[idx]['uid']))
        print("\tSW version is: \t{}".format(dinfo[idx]['swver']))
        print("\tAI version is: \t{}".format(dinfo[idx]['aiver']))
        print("\tHW version is: \t{}".format(dinfo[idx]['hwver']))
        print("\ttimzezone is: \t{}".format(dinfo[idx]['tzone']))
        print("\tfirst bound: \t{}".format(dinfo[idx]['activated']))
        ## print subscription plan
        print("\t[Subscription Status]")
        if len(pinfo) == 0:
            print("\t  No any subscription plan")
        for nn in range(len(pinfo)):
            print("\t  {no} subscription plan:".format(no=nn+1))
            print("\t    store: {}; from <{stime}> to <{etime}>".format(pinfo[nn]['store'],stime=pinfo[nn]['start'], etime=pinfo[nn]['end']))
    ## account information in VSaaS
    print("\n  **** account ({email}) VSaaS information ****".format(email=uinfo['mymail']))
    print("\tAccess Token (VSaaS):\t"+uinfo['vatoken'])
    if len(contractlist) == 0:
        print("    ('︵') User has no available VSaaS contract (failed to create or expired)")

    for kkk in range(len(contractlist)):
        print("    == {cno} VSaaS Contract Information ==".format(cno=kkk+1))
        print("       contract is <{}>; created at: {}; expires at: {}".format(contractlist[kkk]['state'],contractlist[kkk]['created'],contractlist[kkk]['expired']))
        print("       current storage size is: {}G; maximum storage size is: {}G".format(round(contractlist[kkk]['usage'],2),contractlist[kkk]['quantity']))
        print("       current bound devices is: {}; maximum bound devices is: {}".format(contractlist[kkk]['nowbound'], contractlist[kkk]['maxbound']))
        for jjj in range(len(contractlist[kkk]['uids'])):
            print("     - UID of {vno} bound device is: {uid}".format(vno=jjj+1, uid=contractlist[kkk]['uids'][jjj]))
    #### credential and stoken
    if len(devlist) != 0:
        vsaasurl = getVSaaS_url(sku)
        nowdt = datetime.now()
        edt = int(nowdt.timestamp())*1000
        sdt = edt-86400000
        cur_tz = checkTimezone(dinfo[0]['tzone'])
        for kkk in range(len(devlist)):
            print("       VSaaS FW version is %s"%(devlist[kkk]['fw_ver']))
            if devlist[kkk]['uid'] != '':
                bstr = base64.b64decode(devlist[kkk]['credential'])
                credential = str(bstr, "utf-8")
                print("       credential is %s"%(credential))
                print("       vsaasinfo is %s/api/v1/stream/original/contract_info/%s?stoken=%s" % (vsaasurl, devlist[kkk]['uid'], devlist[kkk]['st']))
            else:
                print("       <error> UID of ({}) binding device is empty".format(kkk+1))
                continue
    #### dump events in vsaas in last 24 hours
            eventlist = queryEventList_vsaas(sku, atoken_vsaas, devlist[kkk]['uid'], sdt, edt)
            if len(eventlist) == 0:
                print("\t('︵') Device {} has no event records in past 24 hours ({} ~ {})".format(devlist[kkk]['uid'], datetime.fromtimestamp(sdt//1000, pytz.timezone(cur_tz)), datetime.fromtimestamp(edt//1000, pytz.timezone(cur_tz))))
            else:
                #print(eventlist)
                bindingServer = getBindingServer_vsaas(sku, atoken_vsaas, devlist[kkk]['uid'])
                print("\t-- Device ({}) events records in past 24 hours ({} ~ {})".format(devlist[kkk]['uid'], datetime.fromtimestamp(sdt//1000, pytz.timezone(cur_tz)), datetime.fromtimestamp(edt//1000, pytz.timezone(cur_tz))))
                print("\t  binding server is: https://{}".format(bindingServer))
                for iii in range(len(eventlist)):
                    evt = eventlist[iii]
                    print("\t  event (%d): type is <%d>; created at %s; expired at %s"%(iii+1, evt['event_type'], evt['created'], evt['expires']))
                    print("\t  event pk is {}; start time at {}; timestamp is {}".format(evt['pk'],datetime.fromtimestamp(int(evt['start_time_ts'])//1000, pytz.timezone(cur_tz)), evt['start_time_ts']))
                    #m3u8 = getDownloadURL_vsaas(atoken_vsaas, bindingServer, devlist[kkk]['uid'], evt['start_time_ts'])
                    #print("\t  m3u8: {}".format(m3u8))
    ## check UID in pixsee and VSaaS
    isFound = 0
    if len(dinfo) != len(contractlist):
        print("\n<xxx WARNING xxx> The number of UIDs in pixsee cloud ({len1}) and VSaaS server ({len2}) is different, suggest to check!\n".format(len1=len(dinfo), len2=len(contractlist)))
    else:
        for iii in range(len(dinfo)):
            thisuid = dinfo[iii]['uid']
            for jjj in range(len(contractlist)):
                if thisuid == contractlist[jjj]['uids']:
                    isFound = 1
                if isFound == 1:
                    break
            if isFound == 1:
                break
    if isFound == 1:
        print("\n<xxx WARNING xxx> The UID in pixsee cloud can not be found in VSaaS server, need to check!\n")

    ## 2nd layer sub-menus
        ## v5, check if this babyid was shared by other
    for thisidx in range(len(dinfo)):
        if dinfo[thisidx]['inviter'] != '':
            continue
        ###
        thissn = dinfo[thisidx]['sn']
        thisuid = dinfo[thisidx]['uid']
        thisvtoken = uinfo['vatoken']
        thisatoken = uinfo['atoken']
        thisbaby = dinfo[thisidx]['babyid']
        thistz = cur_tz
        break
    while True:
        byebye = False
        whichone = secondMenu(thissn)
        if whichone == 1:       ## continue checking next account/SN
            break
        elif whichone == 0:     ## Close this utility
            byebye = True
            break
        elif whichone == 2:     ## check all bound accounts with device
            ## get all grantcode by SN
            errcode, allgcode = getAllGrantcode_by_sn(sku, thissn)
            if errcode < 0:
                showWarningMessage(errcode)
                continue
            ## get contact list, device list
            #### get access_token from vsaas server
            for iii in range(len(allgcode)):
                ## get bound device uid
                print('\n** the {cno} bound record **\n'.format(cno=iii+1))
                errcode, atoken_pixsee = getAccessToken_pixsee_bygcode(sku, allgcode[iii]['gcode'])
                if errcode < 0:
                    showWarningMessage(errcode)
                    continue
                errcode, uinfo, dinfo, pinfo = getUserDeviceStatus(sku, atoken_pixsee)
                if errcode < 0:
                    print("\tdevice (SN:{sn}) did not bind to any account in pixsee backend\n".format(sn=thissn))
                else:
                    ij = len(dinfo)-1
                    print("\tdevice (SN:{sn}; UID:{uid}) bound to account ({account}) in pixsee backend\n".format(sn=dinfo[ij]['sn'], uid=dinfo[ij]['uid'], account=uinfo['mymail']))
                ## query account informationin VSaaS
                errcode, atoken_vsaas = getAccessToken_vsaas(sku, allgcode[iii]['gcode'])
                if errcode < 0:
                    showWarningMessage(errcode)
                    continue
                ## query account informationin VSaaS
                vsaas_atoken = atoken_vsaas
                contractlist = queryContractInfo_vsaas(sku, atoken_vsaas)
                devlist = queryDeviceList_vsaas(sku, atoken_vsaas)
                ## account information in VSaaS
                print("\tdevice (SN:{sn}) has ever bound to ({account}) in VSaaS".format(sn=thissn, account=allgcode[iii]['email']))
                print("\t  <<<< VSaaS access token >>>> {}".format(atoken_vsaas))
                if len(contractlist) == 0:
                    print("\t\t(:︵:) User has no available VSaaS contract (failed to create or expired)")
                else:
                    print("\t\t('_') User has created following VSaaS contracts")
                    for kkk in range(len(contractlist)):
                        print("\t\t{cno}) VSaaS Contract Information ==".format(cno=kkk+1))
                        print("\t\t  contract is <{}>; created at: {}; expires at: {}".format(contractlist[kkk]['state'],contractlist[kkk]['created'],contractlist[kkk]['expired']))
                        print("\t\t  current storage size is: {}G; maximum storage size is: {}G".format(round(contractlist[kkk]['usage'],2),contractlist[kkk]['quantity']))
                        #print("\t\t  current bound devices is: {}; maximum bound devices is: {}".format(contractlist[kkk]['nowbound'], contractlist[kkk]['maxbound']))
                        for jjj in range(len(contractlist[kkk]['uids'])):
                            print("\t\t  - UID of {vno} bound device is: {uid}".format(vno=jjj+1, uid=contractlist[kkk]['uids'][jjj]))
                        #### credential and stoken
                if len(devlist) == 0:
                    print("\t\t(:︵:) User did not bind any device in VSaaS server")
                for kkk in range(len(devlist)):
                    print("\t\t  {cno}) bound device ({uid}) in VSaaS server".format(cno=kkk+1, uid=devlist[kkk]['uid']))
                    print("\t\t  VSaaS FW version is %s"%(devlist[kkk]['fw_ver']))
                    bstr = base64.b64decode(devlist[kkk]['credential'])
                    credential = str(bstr, "utf-8")
                    print("\t\t  credential is %s"%(credential))
                    #print("\tvsaasinfo is %s/api/v1/stream/original/contract_info/%s?stoken=%s" % (vsaasurl, devlist[kkk]['uid'], devlist[kkk]['st']))
        elif whichone == 3:     ## check events in VSaaS within a time interval
            print("\n** get event list of %s(%s) from VSaaS server:" % (thissn,thisuid))
            y1, m1, d1, h1, mm1, s1 = input('    Please enter start time <year month day hour minute second> : ').split()
            input_time = datetime(int(y1), int(m1), int(d1), int(h1), int(mm1), int(s1))
            sdt = (input_time.timestamp())*1000
            y2, m2, d2, h2, mm2, s2 = input('    Please enter end time <year month day hour minute second> :   ').split()
            input_time = datetime(int(y2), int(m2), int(d2), int(h2), int(mm2), int(s2))
            edt = (input_time.timestamp())*1000

            eventlist = queryEventList_vsaas(sku, thisvtoken, thisuid, sdt, edt)
            if len(eventlist) == 0:
                print("\t(:︵:) Device {uid} has no event records from {ys}-{ms}-{ds} {hs}:{mms}:{ss} to {ye}-{me}-{de} {he}:{mme}:{se}".format(uid=thisuid, ys=y1, ms=m1, ds=d1, hs=h1, mms=mm1, ss=s1, ye=y2, me=m2, de=d2, he=h2, mme=mm2, se=s2))
            else:
                #print(eventlist)
                bindingServer = getBindingServer_vsaas(sku, thisvtoken, thisuid)
                print("\t-- device {uid} event records from {ys}-{ms}-{ds} {hs}:{mms}:{ss} to {ye}-{me}-{de} {he}:{mme}:{se}".format(uid=thisuid, ys=y1, ms=m1, ds=d1, hs=h1, mms=mm1, ss=s1, ye=y2, me=m2, de=d2, he=h2, mme=mm2, se=s2))
                print("\t   binding server is: https://{}".format(bindingServer))
                for iii in range(len(eventlist)):
                    evt = eventlist[iii]
                    print("\t   event (%d): type is <%d>; created at %s; expired at %s"%(iii+1, evt['event_type'], evt['created'], evt['expires']))
                    print("\t   event pk is {}; start time at {}; timestamp is {}".format(evt['pk'],datetime.fromtimestamp(int(evt['start_time_ts'])//1000, pytz.timezone(thistz)), evt['start_time_ts']))
        elif whichone == 6:     ## delete event from VSaaS server
            print("\n** remove an event of %s(%s) from VSaaS server:" % (thissn,thisuid))
            eid = input('    Please copy designated (eid) from pixsee event list : ')
            pk = input('    Please copy designated (pk) from VSaaS event list : ')
            if eid == '' or pk == '':
                print('\t<! WARNING !> eid or pk should not be empty')
                continue
            retmsg = deleteEvent_pixsee(sku, thisatoken, eid)
            print('\t'+retmsg)
            retmsg = deleteEvent_vsaas(sku, thisvtoken, pk)
            print('\t'+retmsg)
        elif whichone == 4:     ## check events (area & cry) in pixsee within a time interval
            print("\n** get event list of %s(%s) from pixsee backend:" % (thissn,thisuid))
            y1, m1, d1, h1, mm1, s1 = input('   Please enter start time <year month day hour minute second> : ').split()
            input_time = datetime(int(y1), int(m1), int(d1), int(h1), int(mm1), int(s1))
            sdt = (input_time.timestamp())*1000
            y2, m2, d2, h2, mm2, s2 = input('   Please enter end time <year month day hour minute second> :   ').split()
            input_time = datetime(int(y2), int(m2), int(d2), int(h2), int(mm2), int(s2))
            edt = (input_time.timestamp())*1000
            ec_eventlist = getEventHistory(sku, thisatoken, thisbaby, sdt, edt, "ec")
            print("   -- device {sn} event records from {ys}-{ms}-{ds} {hs}:{mms}:{ss} to {ye}-{me}-{de} {he}:{mme}:{se}".format(sn=thissn, ys=y1, ms=m1, ds=d1, hs=h1, mms=mm1, ss=s1, ye=y2, me=m2, de=d2, he=h2, mme=mm2, se=s2))
            if len(ec_eventlist) != 0:
                for ii in range(len(ec_eventlist)):
                    evttime = datetime.fromtimestamp(ec_eventlist[ii]['time']//1000, pytz.timezone(thistz))
                    print("\t{cno}) event ({eid}): ".format(cno=ii+1, eid=ec_eventlist[ii]['eid']))
                    print("\t    type is ({etype}); triggered at {ctime}".format(etype=ec_eventlist[ii]['type'], ctime=evttime))
            else:
                print("   (:︵:) no event records in pixsee backend")
        elif whichone == 5:     ## check photos in pixsee within a time interval
            print("\n** get photo list of %s(%s) from pixsee backend:" % (thissn,thisuid))
            y1, m1, d1, h1, mm1, s1 = input('   Please enter start time <year month day hour minute second> : ').split()
            input_time = datetime(int(y1), int(m1), int(d1), int(h1), int(mm1), int(s1))
            sdt = (input_time.timestamp())*1000
            ttime, photolist = syncPhotos(sku, thisatoken, thisbaby, sdt)
            syncto = datetime.fromtimestamp(ttime//1000, pytz.timezone(thistz))
            print("   -- device {sn} captured photos from {ys}-{ms}-{ds} {hs}:{mms}:{ss} to {till}".format(sn=thissn, ys=y1, ms=m1, ds=d1, hs=h1, mms=mm1, ss=s1, till=syncto))
            print("      total: {num} photos".format(num=len(photolist)))
            if len(photolist) != 0:
                for kkk in range(len(photolist)):
                    timec = datetime.fromtimestamp(photolist[kkk]['time']//1000, pytz.timezone(thistz))
                    timeu = datetime.fromtimestamp(photolist[kkk]['update']//1000, pytz.timezone(thistz))
                    print("\t{cno}) photo ({fid}) :".format(cno=kkk+1, fid=photolist[kkk]['fid']))
                    print("\t  captured at {ctime}; updated at {utime}".format(ctime=timec,utime=timeu))
    ## end of 2nd menu
    if byebye == True:
        print('\n**** See you soon! ****\n')
        break
