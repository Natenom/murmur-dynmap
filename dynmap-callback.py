#!/usr/bin/env python
# -*- coding: utf-8
#
# dynmap-callbacks.py - Uses callbacks in Ice to regenerate the OpenLayersMap whenever
# someone connects/disconnects (using dynmap.py).
#
# Copyright (c) 2010, Natenom / Natenom@googlemail.com
# Version: 0.0.7
# 2010-09-08

## SETTINGS ##
dynmaptxt="/var/www/dokuwiki/data/pages/mumble/dynmap.txt" #Target file.
icesecret="secureme"
iceslice='/usr/share/slice/Murmur.ice'
## DO NOT EDIT BELOW THIS LINE ##


import Ice, sys
Ice.loadSlice("-I/usr/share/slice/ %s" % iceslice)
import Murmur

import dynmap
import time

class MetaCallbackI(Murmur.MetaCallback):
    def started(self, s, current=None):
        print "started"
        serverR=Murmur.ServerCallbackPrx.uncheckedCast(adapter.addWithUUID(ServerCallbackI(server, current.adapter)))
        s.addCallback(serverR)

    def stopped(self, s, current=None):
        print "stopped"

class ServerCallbackI(Murmur.ServerCallback):
    global icesecret
    def __init__(self, server, adapter):
      self.server = server

    def writemapfile(self):
        '''Creates the map and writes it to the target file in the dokuwiki system.'''
        olmap=dynmap.makemap(self.server, True)  #True = nur online user darstellen
        
	try:
	    datei = open(dynmaptxt, "w")
	    datei.write("======Dynamische Mumble-Benutzerkarte (Live)======\n"+olmap+"\n\nAktualisiert %s" % str(time.asctime()))
	    datei.close()
	except:
	    print "Could not write to file."

    def userConnected(self, p, current=None):
	if p.userid != -1: #Ignore unregistered users.
	    self.writemapfile()
	    
    def userDisconnected(self, p, current=None):
	if p.userid != -1: #Ignore unregistered users.
	    self.writemapfile()
    
    def userStateChanged(self, p, current=None):
      print "stateChanged"
      
    def channelCreated(self, c, current=None):
      print "Channel created"

    def channelRemoved(self, c, current=None):
      print "Channel removed."

    def channelStateChanged(self, c, current=None):
      print "channelStateChanged"


if __name__ == "__main__":
    global contextR
    
    
    prop = Ice.createProperties(sys.argv)
    prop.setProperty("Ice.ImplicitContext", "Shared")
    idd = Ice.InitializationData()
    idd.properties = prop
    ice = Ice.initialize(idd)
    ice.getImplicitContext().put("secret", icesecret) # If icesecret is set, we need to set it here as well.
    print "Creating callbacks...",
    meta = Murmur.MetaPrx.checkedCast(ice.stringToProxy('Meta:tcp -h 127.0.0.1 -p 60000'))
    adapter = ice.createObjectAdapterWithEndpoints("Callback.Client", "tcp -h 127.0.0.1")
    metaR=Murmur.MetaCallbackPrx.uncheckedCast(adapter.addWithUUID(MetaCallbackI()))
    adapter.activate()
    meta.addCallback(metaR)

    for server in meta.getBootedServers():
      serverR=Murmur.ServerCallbackPrx.uncheckedCast(adapter.addWithUUID(ServerCallbackI(server, adapter)))
      server.addCallback(serverR)

    print "Done"
    print 'Script running (press CTRL-C to abort)';
    try:
        ice.waitForShutdown()
    except KeyboardInterrupt:
        print 'CTRL-C caught, aborting'

    meta.removeCallback(metaR)
    ice.shutdown()
    print "Goodbye"
