## check user/device information through account (email) or serial number
## by querying pixsee/vsaas tokens from JSON files 
## Philip Wu, 2021-11-09
##
import requests
import base64
from datetime import datetime
import pytz
import json
import getdatabyadmin as ipg

def whichEnv():
    sku = 0                     # default environment
    def_tz = 'Asia/Taipie'      # default timezone
    needInput = True
    while needInput:
        try:
            sku = int(input('  which environment? (0: staging; 1: pixm01-TW; 2: pixm01-US; 3: pixm02) > '))
        except ValueError:
            print("\t<FATAL> Please enter an integer, try it again")
            continue
        if sku == 0:
            whichsku = 'staging'
            needInput = False
        elif sku == 1:
            whichsku = 'tw'
            needInput = False
        elif sku == 2:
            whichsku = 'us'
            needInput = False
        elif sku == 3:
            whichsku = 'cn'
            def_tz = "Asia/Shanghai"    ## default timezone
            needInput = False
        else:
            print('\t<Warning> Please enter a (0~3) integer\n')
    return whichsku, def_tz

def readJSONdata(jfile):
    rfname = jfile
    with open(rfname) as json_file:
        jdata = json.load(json_file)
    return jdata

def findIndexInCurrentAccounts(sku, userdata):
    atoken = ''
    vtoken = ''
    babyid = ''
    errcode = 0
    ## load current JSON (account) file for querying token
    if sku == 'staging':
        skumodel = 'staging_'
    elif sku == 'tw' or sku == 'us':
        skumodel = 'pixm01_'
    elif sku == 'cn':
        skumodel = 'pixm02_'
    ufname = './updatedaily/'+skumodel+'account.json'
    dfname = './updatedaily/'+skumodel+'devices.json'
    ## check serial number or account (email)
    if userdata.find('@') == -1:    ## it's serialnumber
        notEmail = True
        sno = userdata
        who = ''
    else:
        notEmail = False
        sno = ''
        who = userdata

    didx = -1
    djson = readJSONdata(dfname)
    if notEmail == True:    ## user input serial number
        for ii in reversed(range(len(djson['data']))):
            if sno == djson['data'][ii]['sno']:
                who = djson['data'][ii]['owner']
                didx = ii
                break
    if didx != -1 or notEmail == False: ## sno matched, or, user input email
        ajson = readJSONdata(ufname)
        ## debug ##
        print('({ss}) index is {ii}, {ww}'.format(ss=sno, ii=didx, ww=who))
        print(ajson['data'][didx]['account'])
        if notEmail == True:
            who = ajson['data'][didx]['account']
            errcode = 0
        else:
            for ii in reversed(range(len(ajson['data']))):
                if who == ajson['data'][ii]['account']:
                    sno = djson['data'][ii]['sno']
                    errcode = 0
                    didx = ii
                    break
        atoken = ajson['data'][didx]['token']
        vtoken = ajson['data'][didx]['vsaastoken']
        babynum = len(ajson['data'][didx]['babies'])
        babyid = ''
        if babynum > 1:
            print('\t**** <issue> {} ({}) has more than one baby'.format(who, sno))
        elif babynum == 0:
            print('\t**** <issue> {} ({}) didn not register any baby'.format(who, sno))
        else:
            babyid = ajson['data'][didx]['babies'][0]['id']
    else:
        errcode = -1
    return errcode, atoken, vtoken, babyid, who, sno

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
        if len(bb) > 1:
            print('\t== the {} baby information:'.format(ii+1))
        print('\t\tbaby ID is {}'.format(bb[ii]['babyid']))
        if bb[ii]['shared'] != '':
            print('\t\tthis baby is shared by {}'.format(bb[ii]['shared']))
        if bb[ii]['inappp'] == False:
            print('\t\tthis baby has no subscription plan')
        else:
            if len(dd) < 1:
                print('****<warning>**** Something wrong: {} did not bound any device'.format(aa['mymail']))
            elif len(dd) > 1:
                print('****<warning>**** Something wrong: {} bound more than 2 devices'.format(aa['mymail']))
            else:
                thistzone = ipg.checkTimezoneString(dd[0]['tzone'])
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
        if len(dd) > 1:
            print('\t== the {} device information:'.format(ii+1))
        if dd[ii]['serial'] != sno:
            print('\t\tdevice ID is {}'.format(dd[ii]['devid']))
            print('\t\tdevice ({}) UID is {}'.format(dd[ii]['serial'], dd[ii]['tutkid']))
            if bb[ii]['shared'] != '':
                print('\t\tthis device is shared by {}'.format(bb[ii]['shared']))
        else:
            print('\t\tdevice ({}) UID is {}'.format(dd[ii]['serial'], dd[ii]['tutkid']))
            print('\t\tdevice type is {}, model is {}'.format(dd[ii]['dname'], dd[ii]['model']))
            print('\t\tdevice is bound at {}'.format(datetime.fromtimestamp(dd[ii]['bdate'])))
            print('\t\tdevice FW version is {}'.format(dd[ii]['swver']))
            print('\t\tdevice AI version is {}'.format(dd[ii]['aiver']))
            print('\t\tdevice HW version is {}'.format(dd[ii]['hwver']))
            print('\t\tdevice IoT KEY is {}'.format(dd[ii]['iotkey']))
            print('\t\tdevice is located at {}, timezone is {}'.format(dd[ii]['place'], dd[ii]['tzone']))
            if bb[ii]['shared'] != '':
                print('\t\tthis device is shared by {}'.format(bb[ii]['shared']))

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
            for jj in range(len(cc[ii]['udid'])):
                print('\t\t{} bound device is {}'.format(jj+1, cc[ii]['udid'][jj]))
    print('\t  -- binding device information --')
    if len(dd) == 0:
        print('\t\t(:︵:) this contract has no biding devices')
    else:
        for ii in range(len(dd)):
            if len(dd) > 1:
                print('\t\t== the {} binding device information:'.format(ii+1))
            print('\t\tbinding device ({}), VSaaS FW version is {}'.format(dd[ii]['uid'], dd[ii]['fwver']))
            print('\t\tthis binding device is created at {}, updated at {}'.format(datetime.fromtimestamp(dd[ii]['created']), datetime.fromtimestamp(dd[ii]['updated'])))
            print('\t\t[credential] av:{}, ak:{}, identity:{}'.format(dd[ii]['av'],dd[ii]['ak'],dd[ii]['identity']))
## debug
def dumpJSONdata(jdata):
    #json_object = json.loads(jdata)
    json_formatted_str = json.dumps(jdata, indent=4)
    print(json_formatted_str)

##if __name__ == '__main__':
while True:
    userdata = input("  please enter user account (email) or device serial number:> " )
    if userdata.lower() == 'bye':
        print('\n***** See you next time! *****\n')
        break
    model, deftz = whichEnv()

    errcode, atoken, vtoken, babyid, who, sno = findIndexInCurrentAccounts(model, userdata)
    print('  .... user: {}, sno: {}'.format(who, sno))
    if errcode < 0 or sno == '':
        print('\t<warning> Something wrong, can not find this serial number ({})'.format(userdata))
        continue
    ## get account information
    ainfo, binfo, dinfo, sinfo = ipg.getAccountDeviceStatusByToken(model, atoken)
    if ainfo == {} or len(dinfo) == 0:     ## something wrong
        gcode = ipg.getGrandcode(model, who, sno)
        ainfo, binfo, dinfo, sinfo = ipg.getAccountDeviceStatus(model, gcode)
        if ainfo == {}:
            print('\t<warning> Something wrong, can not find this account ({}) by gcode: {}\n'.format(who, gcode))
            continue
    cinfo = ipg.getVsaasContractInfo(model, vtoken)
    if cinfo == []:     ## vsaastoken is invalid
        gcode = ipg.getGrandcode(model, who, sno)
        vtoken, cinfo, vinfo = ipg.getAccountVsaasStatus(model, gcode)
        #nowAccounts['data'][idx]['vtoken'] = vtoken
    else:
        vinfo = ipg.getVsaasDeviceList(model, vtoken)

    ## dump user/device information
    print('\n<<<< current status of ({}) (dev:{})>>>>'.format(ainfo['mymail'], sno))
    #dumpJSONdata(ainfo)
    #dumpJSONdata(binfo)

    dumpinfo(sno, ainfo, binfo, dinfo, sinfo)
    dumpvsaas(vtoken, cinfo, vinfo)

    print('==== next searching ====\n')
