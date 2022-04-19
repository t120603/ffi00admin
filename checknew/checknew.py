###
### load prepared JSON file (from CSV), and fill/add necessary data into
### my data structure for admin analysis
###
import json
#from sqlalchemy import true
import devadmin as me
from datetime import datetime
import pytz

def readJSONdata(jfile):
    rfname = jfile
    with open(rfname) as json_file:
        jdata = json.load(json_file)

    return jdata

def saveToJsonfile(jdata, jfile):
    wfname = './data/'+jfile
    with open(wfname, 'w') as outfile:
        json.dump(jdata, outfile)

def findIndexInCurrentAccounts(who, sno, nowAccounts, isDebug):
    if isDebug == True:
        print('try to find {} ({}) in nowAccounts[]'.format(who, sno))
    for ii in range(len(nowAccounts['data'])):
        if who == nowAccounts['data'][ii]['account']:
            if sno == nowAccounts['data'][ii]['sno']:
                if isDebug == True:
                    print('found ({}) {}, {}'.format(ii+1, nowAccounts['data'][ii]['account'], nowAccounts['data'][ii]['sno']))
                return ii
    if isDebug == True:
        print('{} ({}) is a new comer!'.format(who, sno))
    return -1

def checkNewComer(sku, newComer, nowAccounts):
    for ij in range(len(newComer)):
        sno = newComer[ij]['serial']
        who = newComer[ij]['account']
        print('\n>>>> querying {} new binding status of {} ({})'.format(ij+1, who, sno))
        ## get grand code using Admin API 
        gcode = me.getGrantcode(sku, who, sno)
        #print('\tgrand code of {} is {}'.format(who, gcode))
        ## get account status by grand code
        ainfo, binfo, dinfo, sinfo = me.getAccountDeviceStatus(sku, gcode)
        ## debug
        #print('**** binding status of {} new bound device ****'.format(ij+1))
        #if ainfo == {} or len(binfo) == 0 or len(dinfo) == 0:
        if ainfo == {} or len(binfo) == 0 or len(dinfo) == 0:
            print('  <<<< ERROR >>>> {}({}) cannot find any information by gcode({})'.format(who, sno, gcode))
            continue
        dumpinfo(sno, ainfo, binfo, dinfo, sinfo)
        ## get account information in VSaaS
        vtoken, cinfo, vinfo = me.getAccountVsaasStatus(sku, gcode)
        dumpvsaas(vtoken, cinfo, vinfo)
        ## add new comers into JSON file
        thisuser = {}
        thisuser['account'] = ainfo['mymail']
        thisuser['userid'] = ainfo['openid']
        thisuser['atoken'] = ainfo['atoken']
        if len(binfo) > 1:
            print('  << information >> {} has more than one baby account'.format(ainfo['mymail']))
            #continue
        if len(binfo) != 0:
            thisuser['babyid'] = binfo[0]['babyid']
        kk = 0
        if len(dinfo) > 1:
            print('  ***<warning>*** {} bound more than one devices !!'.format(ainfo['mymail']))
            ## 2022-2-5 added by Philip
            f_eureka = False
            for kk in range(len(dinfo)):
                if dinfo[kk]['serial'] == sno:
                    f_eureka = True
                    break
            if f_eureka == False:
                print('  ***<something wrong>*** cannot find indicated serial number {} !!'.format(sno))
                continue
        if len(dinfo) != 0:
            thisuser['babyid'] = dinfo[kk]['babyid']
            thisuser['deviceid'] = dinfo[kk]['devid']
            thisuser['sno'] = dinfo[kk]['serial']
            thisuser['uid'] = dinfo[kk]['tutkid']
            thisuser['vtoken'] = vtoken
            nowAccounts['data'].append(thisuser)
    return nowAccounts

def checkOldBound(sku, oldUsers, nowAccounts, isDebug):
    ## check updates
    for ii in range(len(oldUsers)):
        sno = oldUsers[ii]['serial']
        who = oldUsers[ii]['account']
        print('\n>>>> querying old binding status of {} ({})'.format(who, sno))
        idx = findIndexInCurrentAccounts(who, sno, nowAccounts, isDebug)
        if idx == -1:
            print('***<warning>*** {} was not in current account JSON file !'.format(who))
            gcode = me.getGrantcode(sku, who, sno)
            ainfo, binfo, dinfo, sinfo = me.getAccountDeviceStatus(sku, gcode)
            vtoken, cinfo, vinfo = me.getAccountVsaasStatus(sku, gcode)
            ## add new account into JSON file
            thisuser = {}
            thisuser['account'] = ainfo['mymail']
            thisuser['userid'] = ainfo['openid']
            thisuser['atoken'] = ainfo['atoken']
            if len(binfo) > 1:
                print('***<warning>*** {} has more than one baby information !!'.format(ainfo['mymail']))
            found = 0
            thisuser['babyid'] = binfo[found]['babyid']
            if len(dinfo) > 1:
                print('***<warning>*** {} bound more than one devices !!'.format(ainfo['mymail']))
                ## 2022-2-5 added by Philip
                for kk in range(len(dinfo)):
                    if dinfo[kk]['serial'] == sno:
                        found = kk
                        break
                if kk >= len(dinfo):
                    print('  ***<something wrong>*** cannot find indicated serial number {} !!'.format(sno))
                    continue
            thisuser['babyid'] = dinfo[found]['babyid']
            thisuser['deviceid'] = dinfo[found]['devid']
            thisuser['sno'] = dinfo[found]['serial']
            thisuser['uid'] = dinfo[found]['tutkid']
            thisuser['vtoken'] = vtoken
            nowAccounts['data'].append(thisuser)
        else:
            atoken = nowAccounts['data'][idx]['atoken']
            ainfo, binfo, dinfo, sinfo = me.queryAccountDeviceStatus(sku, atoken)
            if ainfo == {}:     ## wrong atoken
                gcode = me.getGrantcode(sku, who, sno)
                ainfo, binfo, dinfo, sinfo = me.getAccountDeviceStatus(sku, gcode)
                ## debug
                if ainfo == {} or len(binfo) == 0 or len(dinfo) == 0:
                    print('  ****<warning> old account {} ({}) cannot find account information (gcode={})'.format(who, sno, gcode))
                    continue
                nowAccounts['data'][idx]['atoken'] = ainfo['atoken']
            vtoken = nowAccounts['data'][idx]['vtoken']
            cinfo = me.getVsaasContractInfo(sku, vtoken)
            if cinfo == []:     ## vsaastoken is invalid
                gcode = me.getGrantcode(sku, who, sno)
                vtoken, cinfo, vinfo = me.getAccountVsaasStatus(sku, gcode)
                nowAccounts['data'][idx]['vtoken'] = vtoken
            else:
                vinfo = me.getVsaasDeviceList(sku, vtoken)
            #print('\n')
        ## debug
        print('<<<< current status of {} device {} >>>>'.format(who, sno))
        dumpinfo(sno, ainfo, binfo, dinfo, sinfo)
        dumpvsaas(vtoken, cinfo, vinfo)
    return nowAccounts

def searchUpdatesInLast48Hours(sku, isDebug):
    where = sku.lower()
    if where == 'cn' or where == 'tw' or where == 'us':
        #datafile = where+'_boundlist.json'
        datafile = 'boundlist_'+where+'.json'
    else:
        datafile = 'boundlist_staging.json'
    oldAccounts = readJSONdata(datafile)

    ## list of current avtivated devices (serial number)
    nowBound = []
    for ii in range(len(oldAccounts['data'])):
        #print('{}) old account is {}'.format(ii+1, oldAccounts['data'][ii]))
        nowuser = {}
        nowuser['who'] = oldAccounts['data'][ii]['account']
        nowuser['sno'] = oldAccounts['data'][ii]['sno']
        nowBound.append(nowuser)
    if isDebug == True:
        dumpJSONdata(nowBound)
    ## find new bound devices
    newComer, oldBound = checkRecentActiveAccount(where, nowBound, isDebug)
    if isDebug == True:
        print('<<<< New Comers >>>>')
        dumpJSONdata(newComer)
        print('<<<< Now Bounds >>>>')
        dumpJSONdata(oldBound)
    ## if candidates not in bound list ==> query relevant data and dump them
    tempAccounts = checkNewComer(where, newComer, oldAccounts)
    ## if candidates in current bound list ==> check relevant data in server and update them
    newAccounts = checkOldBound(where, oldBound, tempAccounts, isDebug)
    ## now.timestamp
    nowdt = datetime.now()
    nzero = datetime(nowdt.year, nowdt.month, nowdt.day, nowdt.hour, nowdt.minute, nowdt.second)
    sts = int(nzero.timestamp())*1000
    newAccounts['lastsync'] = sts
    if isDebug == False:
        saveToJsonfile(newAccounts, datafile)
 
def checkRecentActiveAccount(sku, nowbound, isDebug):
    newCandi = []
    oldBound = []
    ## retrieve recent (from 2 dayes till now) bound accounts/devices
    ulist = me.getRecentBoundAccounts(sku)
    if isDebug == True:
        print('<<<< Recent loing accounts >>>>')
        dumpJSONdata(ulist)
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

def dumpinfo(sno, aa, bb, dd, ss):
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
        enrollstr = 'email/password'
        if ssostr != '':
            enrollstr = enrollstr + ', bound to ' + ssostr
    else:
        enrollstr = aa['enroll']
    print('\t\tthis account was registered by {}'.format(enrollstr))
    ## babies information
    print('\t---- babies information -----')
    for ii in range(len(bb)):
        isShared = False
        if len(bb) > 1:
            print('\t  == the {} baby information:'.format(ii+1))
        print('\t\tbaby ID is {}'.format(bb[ii]['babyid']))
        if bb[ii]['shared'] != '':
            print('\t\tthis baby is shared by {}'.format(bb[ii]['shared']))
            isShared = True
        if bb[ii]['inappp'] == False:
            print('\t\tthis baby has no subscription plan')
        elif isShared == False:
        #else:
            ij = 0
            for jj in range(len(dd)):
                if bb[ii]['babyid'] == dd[jj]['babyid']:
                    ij = jj
                    break
            if ij >= len(dd):
                print('****<warning>**** Something wrong: {} did not bind any device now'.format(aa['mymail']))
                continue
                #if len(dd) != 0:
                #    tzone = dd[0]['tzone']
                #else:
                #    tzone = 'Asia/Taipei'       ## no device? using default timezone
                #thistzone = me.checkTimezoneString(tzone)
            else:
                thistzone = me.checkTimezoneString(dd[ij]['tzone'])
            for kk in range(len(ss)):
                print('\t\t{} subscribed from {}: '.format(kk+1, ss[kk]['store']))
                stime = datetime.fromtimestamp(ss[kk]['start'], pytz.timezone(thistzone))
                if ss[kk]['until'] == -1:
                    etime = "(-1: no expiration record)"
                else:
                    etime = datetime.fromtimestamp(ss[kk]['until'], pytz.timezone(thistzone))
                print('\t\t\tfrom <{}> till <{}>'.format(stime, etime))        
    ## devices information
    print('\t---- devices information -----')
    for ii in range(len(dd)):
#        if bb[ii]['shared'] != '':
#            continue        ## since this device was shared by other
        if len(dd) > 1:
            print('\t== the {} device information:'.format(ii+1))
## display all devices information
##        if dd[ii]['serial'] != sno:
##            print('\t\tdevice ID is {}'.format(dd[ii]['devid']))
##            print('\t\tdevice ({}) UID is {}'.format(dd[ii]['serial'], dd[ii]['tutkid']))
##            if bb[ii]['shared'] != '':
##                print('\t\tthis device is shared by {}'.format(bb[ii]['shared']))
##        else:
##            print('\t\tdevice ({}) UID is {}'.format(dd[ii]['serial'], dd[ii]['tutkid']))
##            print('\t\tdevice type is {}, model is {}'.format(dd[ii]['dname'], dd[ii]['model']))
##            print('\t\tdevice is bound at {}'.format(dd[ii]['bdate']))
##            print('\t\tdevice FW version is {}'.format(dd[ii]['swver']))
##            print('\t\tdevice AI version is {}'.format(dd[ii]['aiver']))
##            print('\t\tdevice HW version is {}'.format(dd[ii]['hwver']))
##            print('\t\tdevice IoT KEY is {}'.format(dd[ii]['iotkey']))
##            print('\t\tdevice is located at {}, timezone is {}'.format(dd[ii]['place'], dd[ii]['tzone']))
        print('\t\tthis device is owned by {}'.format(dd[ii]['babyid']))
        print('\t\tdevice ID is {}'.format(dd[ii]['devid']))
        print('\t\tdevice ({}) UID is {}'.format(dd[ii]['serial'], dd[ii]['tutkid']))
        print('\t\tdevice type is {}, model is {}'.format(dd[ii]['dname'], dd[ii]['model']))
        print('\t\tdevice is bound at {}'.format(dd[ii]['bdate']))
        print('\t\tdevice FW version is {}'.format(dd[ii]['swver']))
        print('\t\tdevice AI version is {}'.format(dd[ii]['aiver']))
        print('\t\tdevice HW version is {}'.format(dd[ii]['hwver']))
        print('\t\tdevice IoT KEY is {}'.format(dd[ii]['iotkey']))
        print('\t\tdevice is located at {}, timezone is {}'.format(dd[ii]['place'], dd[ii]['tzone']))
        for kk in range(len(bb)):
            if bb[kk]['babyid'] == dd[ii]['babyid']:
                if bb[kk]['shared'] != '':
                    print('\t\t>>>> this device is shared by {}'.format(bb[kk]['shared']))

def dumpvsaas(token, cc, dd):
    print('\t---- VSaaS information ----')
    print('\t\tVSaaS access token is {}'.format(token))
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
    debugMode = False
    if debugMode == True:
        ## check STAGING
        print('\n==========  STAGING  ==========')
        searchUpdatesInLast48Hours('staging', debugMode)
    else:
        ## check PIXM02
        print('\n========== PIXM02-CN ==========')
        searchUpdatesInLast48Hours('cn', debugMode)
        ## check STAGING
        print('\n==========  STAGING  ==========')
        searchUpdatesInLast48Hours('staging', debugMode)
        ## check PIXM01 (TW & US)
        print('\n========== PIXM01-TW & PIXM01-US ==========')
        searchUpdatesInLast48Hours('tw', debugMode)
