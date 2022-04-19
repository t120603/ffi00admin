###
### load prepared JSON file (from CSV), and fill/add necessary data into
### my data structure for admin analysis
###
import json
import devadmin as me
from datetime import datetime
import pytz

def readJSONdata(jfile):
    with open(jfile) as json_file:
        jdata = json.load(json_file)

    return jdata

def saveToJSONfile(jdata, jfile):
    with open('data/'+jfile, 'w') as outfile:
        json.dump(jdata, outfile)

def isAccountAlreadyExisted(who, aaa):
    fFound = -1
    for ii in range(len(aaa)):
        if who == aaa[ii]['account']:
            fFound = ii
            break
    return fFound

def storeNewComer(sku, newComer, ajson, bjson, djson, vjson):
    for ij in range(len(newComer)):
        sno = newComer[ij]['serial']
        who = newComer[ij]['account']
        ## check whether this 'new account' already existed???
        idx = findIndexInBoundUsers(sno, who, djson)
        if idx != -1:
            print('  <<<< ERROR >>>> new comer {}({}) already existed in device_json'.format(who, sno))
            ajson.pop(idx)
            bjson.pop(idx)
            djson.pop(idx)
            vjson.pop(idx)
        ## get grand code using Admin API 
        gcode = me.getGrantcode(sku, who, sno)
        #print('\tgrand code of {} is {}'.format(who, gcode))
        ## get account status by grand code
        ainfo, binfo, dinfo, sinfo = me.getAccountDeviceStatus(sku, gcode)
        ## debug
        if ainfo == {} or len(binfo) == 0 or len(dinfo) == 0:
            print('  <<<< ERROR >>>> {}({}) cannot find any information by gcode({})'.format(who, sno, gcode))
            continue
        print('\n**** binding status of ({}) new user {}({}) new bound device ({}):'.format(ij+1, ainfo['myname'], ainfo['mymail'], sno))
        
        dumpinfo(ainfo, binfo, dinfo, sinfo)
        ## get account information in VSaaS
        vtoken, cinfo, vinfo = me.getAccountVsaasStatus(sku, gcode)
        dumpvsaas(vtoken, cinfo, vinfo)
        ## add new comers into JSON file
        thisaccount = {}
        thisaccount['account'] = who
        thisaccount['userid'] = ainfo['openid']
        thisaccount['token'] = ainfo['atoken']
        thisaccount['vsaastoken'] = vtoken
        thisaccount['role'] = ''
        thisaccount['rolenote'] = ''
        ssostr = ''
        if ainfo['wechat'] == True:
            ssostr = 'WeChat(SSO)'
        if ainfo['applid'] == True:
            ssostr = 'AppleID(SSO)'
        thisaccount['enroll'] = ainfo['enroll']
        thisaccount['ssovendor'] = ssostr

        if len(binfo) > 1:
            print('  << information >> {} has more than one baby account'.format(ainfo['mymail']))
            #dumpJSONdata(binfo)
            #continue
        thisaccount['babies'] = []
        for ii in range(len(binfo)):
            infant = {}
            infant['id'] = binfo[ii]['babyid']
            infant['owner'] = binfo[ii]['shared']    ## ## this owner means shared by other (i.e. owner)
            thisaccount['babies'].append(infant)

        thisbaby = {}
        thisbaby['babyid'] = binfo[ii]['babyid']
        thisbaby['owner'] = who
        thisbaby['nationality'] = binfo[ii]['nation']
        thisbaby['invitor'] = binfo[ii]['shared']
        
        thisbaby['subscription'] = []
        if binfo[ii]['inappp'] == True:
            for kk in range(len(sinfo)):
                ss = {}
                ss['vendor'] = sinfo[kk]['store']
                ss['start'] = sinfo[kk]['start']
                ss['dueto'] = sinfo[kk]['until']
                thisbaby['subscription'].append(ss)

        thisbaby['devices'] = []
        thisdevice = {}
        thisvsaas = {}
        if len(dinfo) == 0:
            print('  <<<< ERROR >>>> Oops! {}({}) cannot find any binding device information'.format(who, sno))
            thisdevice['deviceid'] = ''
            thisdevice['owner'] = who
            thisdevice['sno'] = ''
            thisdevice['tutkid'] = ''
            thisdevice['FWver'] = ''
            thisdevice['AIver'] = ''
            thisdevice['HWver'] = ''
            thisdevice['bounddate'] = 0
            thisdevice['timezone'] = ''
            thisdevice['location'] = ''

            thisvsaas['account'] = who
            thisvsaas['token'] = ''
            thisvsaas['contract'] = {}
        else:
            for jj in range(len(dinfo)):
                if sno == dinfo[jj]['serial']:
                    break
            dd = {}
            dd['tutkid'] = dinfo[jj]['tutkid']
            dd['deviceid'] = dinfo[jj]['devid']
            thisbaby['devices'].append(dd)

            thisdevice['deviceid'] = dinfo[jj]['devid']
            thisdevice['owner'] = who
            thisdevice['sno'] = dinfo[jj]['serial']
            thisdevice['tutkid'] = dinfo[jj]['tutkid']
            thisdevice['FWver'] = dinfo[jj]['swver']
            thisdevice['AIver'] = dinfo[jj]['aiver']
            thisdevice['HWver'] = dinfo[jj]['hwver']
            thisdevice['bounddate'] = dinfo[jj]['bdate']
            thisdevice['timezone'] = dinfo[jj]['tzone']
            thisdevice['location'] = dinfo[jj]['place']
            
            thisvsaas['account'] = who
            thisvsaas['token'] = vtoken
            thisvsaas['contract'] = {}
            if len(cinfo) != 0:
                vd = []
                ## find active contract
                cii = 0
                for jj in range(len(cinfo)):
                    if cinfo[jj]['state'] == 'ACTIVATE':
                        cii = jj
                        break
                thiscontract = {}
                thiscontract['contractid'] = cinfo[cii]['pk']
                thiscontract['created'] = cinfo[cii]['created']
                thiscontract['expired'] = cinfo[cii]['expired']
                for jj in range(len(cinfo[cii]['udid'])):
                    dd = {}
                    for kk in range(len(vinfo)):
                        if vinfo[kk]['uid'] == cinfo[cii]['udid'][jj]:
                            dd['bound'] = vinfo[kk]['uid']
                            dd['fwver'] = vinfo[kk]['fwver']
                            dd['ak'] = vinfo[kk]['ak']
                            vd.append(dd)
                thiscontract['devices'] = vd
                thisvsaas['contract'] = thiscontract

        ajson['data'].append(thisaccount)            
        bjson['data'].append(thisbaby)
        djson['data'].append(thisdevice)
        vjson['data'].append(thisvsaas)

    return ajson, bjson, djson, vjson

def updateOldBound(sku, oldUsers, ajson, bjson, djson, vjson):
    ## check updates
    for ii in range(len(oldUsers)):
        sno = oldUsers[ii]['serial']
        who = oldUsers[ii]['account']
        #newmail = False
        print('\n**** current status of bound device ({})({}):'.format(sno,who))
        ## find index in JSON file
        idx = findIndexInBoundUsers(sno, who, djson)
        if idx < 0:
            #print('  ****<warning> User {} device {} can not be found in bound records'.format(who, sno))
            #newmail = True
            gcode = me.getGrantcode(sku, who, sno)
            if gcode == '':
                print(f'  <<<< ERROR >>>> unable to get grant code for {who}({sno}), get help from admin !!')
                continue
            ainfo, binfo, dinfo, sinfo = me.getAccountDeviceStatus(sku, gcode)
            if ainfo == {} or dinfo == []:
                print(f'  <<<< ERROR >>>> unable to get {who}({sno}) account/device information, get help from admain !!')
                continue
            vtoken, cinfo, vinfo = me.getAccountVsaasStatus(sku, gcode)

            if who != ainfo['mymail']:        ## debug purpose
                print(f"  <<<<warning>>>> conflict between email accounts ({who}) vs ({ainfo['mymail']})")
        else:
            ## get access token to retrieve updated information
            atoken = ajson['data'][idx]['token']
            vtoken = vjson['data'][idx]['token']
            ainfo, binfo, dinfo, sinfo = me.getAccountDeviceStatusByToken(sku, atoken)
            if ainfo == {} or dinfo == []:     ## maybe access token is expired
                gcode = me.getGrantcode(sku, who, sno)
                if gcode == '':
                    print(f'  <<<< ERROR >>>> unable to get grant code for {who}({sno}), get help from admin !!')
                    continue
                ainfo, binfo, dinfo, sinfo = me.getAccountDeviceStatus(sku, gcode)
                if ainfo == {} or dinfo == []:
                    print(f'  <<<< ERROR >>>> unable to get {who}({sno}) account/device information, get help from admain !!')
                    continue
                vtoken, cinfo, vinfo = me.getAccountVsaasStatus(sku, gcode)
            else:
                cinfo = me.getVsaasContractInfo(sku, vtoken)
                if cinfo == []:     ## vsaastoken is invalid
                    gcode = me.getGrantcode(sku, who, sno)
                    vtoken, cinfo, vinfo = me.getAccountVsaasStatus(sku, gcode)
                else:
                    vinfo = me.getVsaasDeviceList(sku, vtoken)
        ### update account information
        if idx < 0:
            print(f'  <<<< ERROR >>>> this condition of {who}({sno}) should not happen, get help from admin !!')
            continue
        
        ajson['data'][idx]['account'] = ainfo['mymail']
        ajson['data'][idx]['userid'] = ainfo['openid']
        ajson['data'][idx]['token'] = ainfo['atoken']
        ajson['data'][idx]['vsaastoken'] = vtoken
        ## updates data in JSON file
        ssostr = ''
        if ainfo['wechat'] == True:
            ssostr = 'WeChat(SSO)'
        if ainfo['applid'] == True:
            ssostr = 'AppleID(SSO)'
        ## dump the updates on SSO
        if ainfo['enroll'] != ajson['data'][idx]['enroll']:
            print('\t{}({}) registered using {}'.format(ainfo['mymail'], sno, ssostr))
        ajson['data'][idx]['enroll'] = ainfo['enroll']
        ajson['data'][idx]['ssovendor'] = ssostr

        if len(binfo) > 1:
            print('  <<<<warning>>>> {} has more than one baby information !!'.format(ainfo['mymail']))
            for ij in range(len(binfo)):
                if binfo[ij]['shared'] == '':   ## not shared by others
                    if binfo[ij]['inappp'] == True:
                        notestr = 'subscribed'
                    else:
                        notestr = 'unsubscribed'
                else:
                    notestr = 'shared by '+binfo[ij]['shared']
                print('\t({}) babyid is {}; {}'.format(ij+1, binfo[ij]['babyid'], notestr))
            #continue
        elif len(binfo) == 0:
            print('  <<<< ERROR >>>> {} has no any baby account !!'.format(ainfo['mymail']))
            continue

        found = 0
        for jj in range(len(binfo)):
            if bjson['data'][idx]['babyid'] == binfo[jj]['babyid']:
                found = jj
                break
        bjson['data'][idx]['babyid'] = binfo[found]['babyid']
        bjson['data'][idx]['nationality'] = binfo[found]['nation']
        bjson['data'][idx]['invitor'] = binfo[found]['shared']
        
        thissubscription = []
        if binfo[found]['inappp'] == True:
            for kk in range(len(sinfo)):
                ss = {}
                ss['vendor'] = sinfo[kk]['store']
                ss['start'] = sinfo[kk]['start']
                ss['dueto'] = sinfo[kk]['until']
                thissubscription.append(ss)
        ## dump information if updates
        if bjson['data'][idx]['subscription'] != thissubscription:
            if len(dinfo) == 0:
                print('  <<<< ERROR >>>> {}({}) did not bind any device ??'.format(ainfo['mymail'], sno))
            else:
                devtzone = ''
                for kk in range(len(dinfo)):
                    if dinfo[kk]['babyid'] == bjson['data'][idx]['babyid']:
                        devtzone = dinfo[kk]['tzone']
                        break
                if devtzone == '':
                    print('  <<<<warning>>>> {}({}) babyid({}) has no associated device ??'.format(ainfo['mymail'], sno, bjson['data'][idx]['babyid']))
                else:
                    sinfo = me.getSubscriptionInfoByBabyid(sku, atoken, bjson['data'][idx]['babyid'])
                    if sinfo != []:
                        dumpSubscription(devtzone, sinfo)
        bjson['data'][idx]['subscription'] = thissubscription
        ### update device information
        if len(dinfo) > 1:
            print('  ***<warning>*** {}({}) bound more than one devices'.format(ainfo['mymail'], binfo[found]['babyid']))
            for ij in range(len(dinfo)):
                print('\t({}) device {}({}) bound to {}'.format(ij+1, dinfo[ij]['serial'], dinfo[ij]['tutkid'], dinfo[ij]['babyid']))
            #continue
        elif len(dinfo) == 0:
            print('  <<<< ERROR >>>> {}({}) does not bind any devices'.format(ainfo['mymail'], binfo[found]['babyid']))
            continue

        found = 0
        for jj in range(len(dinfo)):
            if sno == dinfo[jj]['serial']:
                found = jj
                break
        ## dump information if any change
        if djson['data'][idx]['FWver'] != dinfo[found]['swver'] or djson['data'][idx]['timezone'] != dinfo[found]['tzone']:
            print('\tdevice ({}) UID is {}'.format(dinfo[found]['serial'], dinfo[found]['tutkid']))
            print('\tdevice FW version is {} (<-- {})'.format(dinfo[found]['swver'], djson['data'][idx]['FWver']))
            print('\tdevice is located at {}, timezone is {}'.format(dinfo[found]['place'], dinfo[found]['tzone']))
        ### renew JSON recored
        djson['data'][idx]['deviceid'] = dinfo[found]['devid']
        djson['data'][idx]['owner'] = who
        djson['data'][idx]['sno'] = dinfo[found]['serial']
        djson['data'][idx]['tutkid'] = dinfo[found]['tutkid']
        djson['data'][idx]['FWver'] = dinfo[found]['swver']
        djson['data'][idx]['AIver'] = dinfo[found]['aiver']
        djson['data'][idx]['HWver'] = dinfo[found]['hwver']
        djson['data'][idx]['bounddate'] = dinfo[found]['bdate']
        djson['data'][idx]['timezone'] = dinfo[found]['tzone']
        djson['data'][idx]['location'] = dinfo[found]['place']
            
        vjson['data'][idx]['account'] = ainfo['mymail']
        vjson['data'][idx]['token'] = vtoken
        thiscontract = {}
        foundUID = False
        if len(cinfo) != 0:
            vd = []
            ## find active contract
            cii = 0
            for jj in range(len(cinfo)):
                if cinfo[jj]['state'] == 'ACTIVATE':
                    cii = jj
                    break

            thiscontract['contractid'] = cinfo[cii]['pk']
            thiscontract['created'] = cinfo[cii]['created']
            thiscontract['expired'] = cinfo[cii]['expired']
            for jj in range(len(cinfo[cii]['udid'])):
                dd = {}
                for kk in range(len(vinfo)):
                    if vinfo[kk]['uid'] == cinfo[cii]['udid'][jj]:
                        dd['bound'] = vinfo[kk]['uid']
                        dd['fwver'] = vinfo[kk]['fwver']
                        dd['ak'] = vinfo[kk]['ak']
                        vd.append(dd)
                        foundUID = True
            thiscontract['devices'] = vd
        if len(thiscontract) != 0 or foundUID == True:
            #print(vjson['data'][idx]['contract'])
            if vjson['data'][idx]['contract'] != thiscontract or vjson['data'][idx]['contract']['expired'] != cinfo[cii]['expired']:
                print('\tdevice UID is {}; sno is {}'.format(djson['data'][idx]['tutkid'], djson['data'][idx]['sno']))
                dumpvsaas(vtoken, cinfo, vinfo)
        vjson['data'][idx]['contract'] = thiscontract
    return ajson, bjson, djson, vjson

def findIndexInBoundUsers(sno, who, myDD):
    idx = -1
    for ii in reversed(range(len(myDD['data']))):
        #debug
        #print('\t\t\t<<<< ({}) {}, {} >>>>'.format(ii+1, myDD['data'][ii]['owner'], myDD['data'][ii]['sno']))
        if who == myDD['data'][ii]['owner'] and sno == myDD['data'][ii]['sno']:
            idx = ii
            break
    return idx

def findIndexInBoundSerialNumber(sno, myDD):
    idx = -1
    for ii in range(len(myDD['data'])):
        if sno == myDD['data'][ii]['sno']:
            idx = ii
            break
    return idx

def searchUpdatesInLast48Hours(sku):
    where = sku.lower()
    if where == 'cn':
        prefix = 'pixm02'
    elif where == 'tw' or where == 'us':
        prefix = 'pixm01'
    else:
        prefix = 'staging'
    myAccounts = readJSONdata(prefix+'_account.json')
    myBabies = readJSONdata(prefix+'_babies.json')
    myDevices = readJSONdata(prefix+'_devices.json')
    myVsaas = readJSONdata(prefix+'_vsaas.json')

    ## debug
    #dumpJSONdata(myAccounts)
    #dumpJSONdata(myBabies)
    #dumpJSONdata(myDevices)
    #dumpJSONdata(myVSaaS)

    ## list of current avtivated devices (serial number)
    nowBound = []
    for ii in range(len(myDevices['data'])):
        founduser = {}
        founduser['who'] = myDevices['data'][ii]['owner']
        founduser['sno'] = myDevices['data'][ii]['sno']
        nowBound.append(founduser)
    #print(nowBound)
    ## find new bound devices
    newCandi, oldBound = checkRecentActiveAccount(where, nowBound)
    #print(oldBound)
    ## if candidates not in bound list ==> query relevant data and dump them
    myAA, myBB, myDD, myVV = storeNewComer(where, newCandi, myAccounts, myBabies, myDevices, myVsaas)
    ## if candidates in current bound list ==> check relevant data in server and update them
    myAccounts, myBabies, myDevices, myVsaas = updateOldBound(where, oldBound, myAA, myBB, myDD, myVV)
    ## now.timestamp
    nowdt = datetime.now()
    nowts = datetime(nowdt.year, nowdt.month, nowdt.day, nowdt.hour, nowdt.minute, nowdt.second)
    tsts = int(nowts.timestamp())*1000
    myAccounts['updated'] = tsts
    myBabies['updated'] = tsts
    myDevices['updated'] = tsts
    myVsaas['updated'] = tsts
    saveToJSONfile(myAccounts, prefix+'_account.json')
    saveToJSONfile(myBabies, prefix+'_babies.json')
    saveToJSONfile(myDevices, prefix+'_devices.json')
    saveToJSONfile(myVsaas, prefix+'_vsaas.json')

def checkRecentActiveAccount(sku, nowbound):
    newCandi = []
    oldBound = []
    ## retrieve recent (from 2 dayes till now) bound accounts/devices
    ulist = me.getRecentBoundAccounts(sku)
    for ii in range(len(ulist)):
        bbcam = ulist[ii]['devices']
        if len(bbcam) > 0:
            who = ulist[ii]['account']['email']
            for jj in range(len(bbcam)):
                sno = ulist[ii]['devices'][jj]['serialNumber']
                candidate = {}
                eureka = False
                for kk in range(len(nowbound)):
                    if who == nowbound[kk]['who'] and sno == nowbound[kk]['sno']:
                        eureka = True
                        break
                candidate['account'] = who
                candidate['serial'] = sno
                if eureka == True:
                    oldBound.append(candidate)
                else:
                    newCandi.append(candidate)
    return newCandi, oldBound

def dumpJSONdata(jdata):
    #json_object = json.loads(jdata)
    json_formatted_str = json.dumps(jdata, indent=4)
    print(json_formatted_str)

def dumpDeviceinfo(bb, dd):
    print('\t---- devices information -----')
    for ii in range(len(dd)):
        if len(dd) > 1:
            print('\t    == the {} device information:'.format(ii+1))
        print('\t\tdevice ({}) UID is {}'.format(dd[ii]['serial'], dd[ii]['tutkid']))
        ## check if shared by another account
        isShared = False
        for kk in range(len(bb)):
            if bb[kk]['babyid'] == dd[ii]['babyid']:
                if bb[kk]['shared'] != '':
                    isShared = True
                    whoshared = bb[kk]['shared']
                    break

        if isShared == True:
            print('\t\t>>>> this device is shared by {}'.format(whoshared))
        else:
            print('\t\tthis device is owned by {}'.format(dd[ii]['babyid']))
            print('\t\tdevice ID is {}'.format(dd[ii]['devid']))
            print('\t\tdevice type is {}, model is {}'.format(dd[ii]['dname'], dd[ii]['model']))
            print('\t\tdevice is bound at {}'.format(datetime.fromtimestamp(dd[ii]['bdate'])))
            print('\t\tdevice FW version is {}'.format(dd[ii]['swver']))
            print('\t\tdevice AI version is {}'.format(dd[ii]['aiver']))
            print('\t\tdevice HW version is {}'.format(dd[ii]['hwver']))
            print('\t\tdevice IoT KEY is {}'.format(dd[ii]['iotkey']))
            print('\t\tdevice is located at {}, timezone is {}'.format(dd[ii]['place'], dd[ii]['tzone']))

def dumpSubscription(thistzone, ss):
    for kk in range(len(ss)):
        print('\t\t{} subscribed from {}: '.format(kk+1, ss[kk]['store']))
        stime = datetime.fromtimestamp(ss[kk]['start'], pytz.timezone(thistzone))
        if ss[kk]['until'] == -1:
            etime = "(-1: no expiration record)"
        else:
            etime = datetime.fromtimestamp(ss[kk]['until'], pytz.timezone(thistzone))
        print('\t\t\tfrom <{}> till <{}>'.format(stime, etime))        

def dumpinfo(aa, bb, dd, ss):
    print('\tuser {}({}) has {} babies accounts:'.format(aa['myname'], aa['mymail'], len(bb)))
    ## account information
    print('\t---- account information -----')
    print('\t\taccount access token is {}'.format(aa['atoken']))
    print('\t\taccount openID is {}'.format(aa['openid']))
    if aa['shared'] == True:
        print('\t\tthis account is a virtual account')
    ssostr = ''
    if aa['wechat'] == True:
        ssostr = 'WeChat(SSO)'
    if aa['applid'] == True:
        ssostr = 'AppleID(SSO)'
    if aa['enroll'] == 'compal':
        print('\t\tthis account was registered using email/password')
    else:
        print('\t\tthis account was registered by {}'.format(ssostr))
    ## babies information
    print('\t---- babies information -----')
    for ii in range(len(bb)):
        isShared = False
        if len(bb) > 1:
            print('\t\t== the {} baby information:'.format(ii+1))
        print('\t\tbaby ID is {}'.format(bb[ii]['babyid']))
        if bb[ii]['shared'] != '':
            print('\t\tthis baby is shared by {}'.format(bb[ii]['shared']))
            isShared = True
        if bb[ii]['inappp'] == False:
            print('\t\tthis baby has no subscription plan')
        elif isShared == False:
            if len(dd) < 1:
                print('****<warning>**** Something wrong: {} did not bound any device'.format(aa['mymail']))
            elif len(dd) > 1:
                print('****<warning>**** Something wrong: {} bound more than 2 devices'.format(aa['mymail']))
            else:
                thistzone = me.checkTimezoneString(dd[0]['tzone'])
#                for kk in range(len(ss)):
#                    print('\t\t{} subscribed from {}: '.format(kk+1, ss[kk]['store']))
#                    stime = datetime.fromtimestamp(ss[kk]['start'], pytz.timezone(thistzone))
#                    if ss[kk]['until'] == -1:
#                        etime = "(-1: no expiration record)"
#                    else:
#                        etime = datetime.fromtimestamp(ss[kk]['until'], pytz.timezone(thistzone))
#                    print('\t\t\tfrom <{}> till <{}>'.format(stime, etime))
                dumpSubscription(thistzone, ss)
    ## devices information
    dumpDeviceinfo(bb, dd)
#    print('\t---- devices information -----')
#    for ii in range(len(dd)):
#        if len(dd) > 1:
#            print('\t\t== the {} device information:'.format(ii+1))
#        print('\t\tdevice ID is {}'.format(dd[ii]['devid']))
#        print('\t\tdevice ({}) UID is {}'.format(dd[ii]['serial'], dd[ii]['tutkid']))
#        if bb[ii]['shared'] != '':
#            print('\t\tthis device is shared by {}'.format(bb[ii]['shared']))
#        else:
#            print('\t\tdevice type is {}, model is {}'.format(dd[ii]['dname'], dd[ii]['model']))
#            print('\t\tdevice is bound at {}'.format(datetime.fromtimestamp(dd[ii]['bdate'])))
#            print('\t\tdevice FW version is {}'.format(dd[ii]['swver']))
#            print('\t\tdevice AI version is {}'.format(dd[ii]['aiver']))
#            print('\t\tdevice HW version is {}'.format(dd[ii]['hwver']))
#            print('\t\tdevice IoT KEY is {}'.format(dd[ii]['iotkey']))
#            print('\t\tdevice is located at {}, timezone is {}'.format(dd[ii]['place'], dd[ii]['tzone']))

def dumpvsaas(token, cc, dd):
    print('\t---- VSaaS information ----')
    if len(cc) == 0:
        print('\t\t(:︵:) this account has no available VSaaS Contract')
    else:
        for ii in range(len(cc)):
            if len(cc) > 1:
                print('\t\t== the {} contract information:'.format(ii+1))
            print('\t\tcontract (id={}) is ({}), \n\t\t  created at {}, expires at {}'.format(cc[ii]['pk'],cc[ii]['state'], datetime.fromtimestamp(cc[ii]['created']), datetime.fromtimestamp(cc[ii]['expired'])))
            print('\t\tcurrent bound device is {}, contract maximum bound devices is {}'.format(cc[ii]['nowbound'], cc[ii]['maxbound']))
            print('\t\tcurrent consumed storage size is {}G, maximum storage size is {}G'.format(round(cc[ii]['usage'],2), cc[ii]['quantity']))
            if len(cc[ii]['udid']) == 0:
                print('\t\t(:︵:) this contract has no binding devices')
            for jj in range(len(cc[ii]['udid'])):
                print('\t\t{} bound device is {}'.format(jj+1, cc[ii]['udid'][jj]))
    print('\t    -- binding device information --')
    if len(dd) == 0:
        print('\t\t(:︵:) this contract has no biding devices')
    else:
        for ii in range(len(dd)):
            if len(dd) > 1:
                print('\t\t== the {} binding device information:'.format(ii+1))
            print('\t\tbinding device ({}), VSaaS FW version is {}'.format(dd[ii]['uid'], dd[ii]['fwver']))
            print('\t\tthis binding device is created at {}, updated at {}'.format(datetime.fromtimestamp(dd[ii]['created']), datetime.fromtimestamp(dd[ii]['updated'])))
            print('\t\t[credential] av:{}, ak:{}, identity:{}'.format(dd[ii]['av'],dd[ii]['ak'],dd[ii]['identity']))


##
if __name__ == '__main__':
    print('\n========== PIXM02-CN ==========\n')
    searchUpdatesInLast48Hours('cn')
    print('\n==========  STAGING  ==========\n')
    searchUpdatesInLast48Hours('staging')
    print('\n==========  PIXM01   ==========\n')
    searchUpdatesInLast48Hours('tw')
