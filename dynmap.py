#!/usr/bin/env python
# -*- coding: utf-8
#
# dynmap.py - Creates the Data for a dynamic map of online/offline users of a Mumble-Server (Murmur)
# using the DokuWiki-Plugin OpenLayersMap (http://www.dokuwiki.org/plugin:openlayersmap).
#
# Copyright (c) 2010, Natenom / Natenom@googlemail.com
# Version: 0.0.7
# 2010-09-08

## DB Settings ##
sqlitedb='/home/dynmap.sqlite'
##

## THESE Settings are only being needed if we are __main__: ##
iceslice='/usr/share/slice/Murmur.ice' #Path to Murmur.ice
serverport=64738
iceport=60000
icesecret="secureme"
serverid=1
## DO NOT EDIT BELOW THIS LINE ##

from sqlite3 import *

def nohtml(string):
    import re
    '''Removes html tags'''
    ret=str(re.sub(r'<[^>]*?>', '', string))
    return ret

def makemap(server, onlyonline=False, usecommentonly=False):
    '''Durchläuft die Datenbank UserDB und guckt ob der Benutzer online ist in mumble (mittels Ice))'''
    import base64

    sessionID=0
    onlineuser={}
    online=False
    
    onlineusers=server.getUsers()
    
    retvar='[[mumble:tools:benutzerkarte#datenschutz|Datenschutzhinweis und technische Umsetzung]]'
    retvar+="<olmap id=\"olmap\" width=\"700px\" height=\"500px\" lat=\"50.9411\" lon=\"6.9578\" zoom=\"20\" statusbar=\"1\" toolbar=\"1\" controls=\"1\" poihoverstyle=\"0\" baselyr=\"cloudmade map\">\n"
    
    if (usecommentonly==True):
	#extrahieren aus dem Kommentar
	for user in onlineusers:
	    print 
    else:
	#Use Database
	conn = connect(sqlitedb)
	cursor = conn.cursor()
	
	UserDB=cursor.execute('''SELECT userid, name, lat, lon FROM dynmap;''')
	for user in UserDB:
	    avatarimg=''
	    #für jeden Benutzer in unserer coord datenbank alle benutzer von currentusers durchgehen und gucken ob id gleich
	    for onlineuser in onlineusers.iteritems():
		sessionID=0
		#if user['userid'] == onlineuser[1].userid:
		if user[0] == onlineuser[1].userid:
		    online=True
		    sessionID=onlineuser[1].session
		    break
		else:
		    online=False
	    
	    #Avatar des Benutzers holen
	    try:
		avatar=base64.b64encode(server.getTexture(int(user[0])))
	    except:
		avatar=''

	    if avatar:
		#avatarimg="<img width='25px' src='data:image/png;base64,%s' />" % avatar
		avatarstring='<html><img width="50px" src="data:image/png;base64,%s" /></html>' % avatar
		#avatarstring='' ##DEBUG erstmal keine avatare
		#nutzt man hier src='data ... ruft der Browser seltsamerweise die Daten bei der IP-Adresse ab nicht der Domain?!
	    else:
		avatarstring=''
		
	    if sessionID > 0:
		name=nohtml(onlineusers[sessionID].name) #If User is online take name from Mumble.
	    else:
		#name=nohtml(user['name']) #If offline, take the name from our database.
		name=nohtml(user[1]) #If offline, take the name from our database.

	    if online:
		#a_icon="avatar.png"
		#a_status="online"
		retvar+="%s, %s,0,1,avatar.png,%s (%s min online) %s\n" % (user[2], user[3], name, onlineusers[sessionID].onlinesecs/60, avatarstring)
	    else:
		#a_icon="avatar_off.png"
		#a_status="offline"
		if (onlyonline):
		    continue
		else:
		    retvar+="%s, %s,0,1,avatar_off.png,%s (offline) %s\n" % (user[2], user[3], name, avatarstring)
	
	conn.close()
	
    retvar+="</olmap>\n"
    return retvar


if __name__ == '__main__':
    import Ice, sys
    Ice.loadSlice("-I/usr/share/slice/ %s" % iceslice)
    import Murmur

    prop = Ice.createProperties(sys.argv)
    prop.setProperty("Ice.ImplicitContext", "Shared")
    idd = Ice.InitializationData()
    idd.properties = prop
    ice = Ice.initialize(idd)
    ice.getImplicitContext().put("secret", icesecret) # If icesecret is set, we need to set it here as well.

    meta = Murmur.MetaPrx.checkedCast(ice.stringToProxy("Meta:tcp -h 127.0.0.1 -p %s" % (iceport)))
    server=meta.getServer(serverid)

    print makemap(server, True, True)
    ice.shutdown()
