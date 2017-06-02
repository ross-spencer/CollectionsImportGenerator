# -*- coding: utf-8 -*-
import sys
import unicodecsv
import ConfigParser
from os.path import exists

from droidcsvhandlerclass import *

# Table schema code...
sys.path.append(r'JsonTableSchema/')
import JsonTableSchema

class NewRow: 
   checksum = ""
   path = ""
   rdict = {}

class ExternalCSVHandler:

   #place to store cfg loc
   configfile = False

   #config section in cfg
   mapconfig = "external mapping config"
   
   #mapping section in cfg
   mapping = "external mapping"

   pathcolumn = "PathColumn"
   checksumcolumn = "ChecksumColumn"
   pathmask = "Mask"

   rowdict = {}
   maphead = []

   def __init__(self, configfile, importschema):
      self.config = ConfigParser.RawConfigParser()  
      
      self.configfile = configfile         
      self.importschema = importschema         

      self.__getconfig__()
      self.__getheaders__()
      
      self.__getmappingtable__()
      
   def __getconfig__(self):
      sys.stderr.write("Mapping config being read from: " + self.configfile + "\n")
      self.config.read(self.configfile)   
      self.pathmask = self.config.get(self.mapconfig, self.pathmask)
      self.checksumcol = self.config.get(self.mapconfig, self.checksumcolumn)      
      self.pathcol = self.config.get(self.mapconfig, self.pathcolumn)      
      return

   def __getheaders__(self):
      sys.stderr.write("Import schema being read from: " + self.importschema + "\n")
      f = open(self.importschema, 'rb')        
      importschemajson = f.read()
      importschema = JsonTableSchema.JSONTableSchema(importschemajson)
      self.importheaders = importschema.as_list()         
      f.close()
      return
      
   def __getmappingtable__(self):
      for i in self.importheaders:
         if self.config.has_option(self.mapping, i):            
            mapvalue = self.config.get(self.mapping, i)
            if mapvalue is not "":
               self.maphead.append(mapvalue)
               if len(mapvalue.split(",")) > 1:
                  for j in mapvalue.split(","):
                     self.rowdict[j] = i
               else:
                  self.rowdict[mapvalue] = i

      print self.rowdict

   def readExternalCSV(self, extcsvname):   
      augmented = []    #augmented metadata
      exportlist = None
      if exists(extcsvname):
         csvhandler = genericCSVHandler()
         exportlist = csvhandler.csvaslist(extcsvname)
         #counter a blank sheet
         if len(exportlist) < 1:
            exportlist = None
         if exportlist is not None:
            for e in exportlist:                        
               row = NewRow()
               if e[self.checksumcol] != "":
                  row.checksum = e[self.checksumcol]
               if e[self.pathcol] != "":
                  row.path = e[self.pathcol].replace(self.pathmask, "")
               for f in e:
                  if f in self.maphead:
                     row.rdict[e[f]] = self.rowdict[f]
               augmented.append(row)
      return augmented