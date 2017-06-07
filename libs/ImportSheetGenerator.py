# -*- coding: utf-8 -*-
import sys
import ConfigParser
from datetime import datetime
from droidcsvhandlerclass import *

# Table schema code...
sys.path.append(r'JsonTableSchema/')
import JsonTableSchema

class ImportSheetGenerator:

   def __init__(self, droidcsv, importschema, configfile):
      self.config = ConfigParser.RawConfigParser()      
      if configfile is not False and configfile is not None:
         self.config.read(configfile)   
         self.pathmask = self.config.get('additional values', 'pathmask')  
      self.droidcsv = droidcsv
      self.importschema = importschema
   
   def setExternalCSV(self, externalCSV):
      if externalCSV != None:
         self.externalCSV = externalCSV
      else:
         self.externalCSV = None
   
   def retrieve_year_from_modified_date(self, MODIFIED_DATE):
      year = ""
      if MODIFIED_DATE != '':
         inputdateformat = '%Y-%m-%dT%H:%M:%S'
         year = datetime.strptime(MODIFIED_DATE, inputdateformat).year
      else:
         sys.stderr.write("Date field used to extrave 'year' is blank.")
      return year

   def add_csv_value(self, value):
      field = ''
      if type(value) is int:              #TODO: probably a better way to do this (type-agnostic)
         field = '"' + str(value) + '"'
      else:
         field = '"' + value.encode('utf-8') + '"'
      return field

   def get_path(self, path):
      return path.replace(self.pathmask, "")

   def get_title(self, title):
      return title.rsplit('.', 1)[0].rstrip()  #split once at full-stop (assumptuon 'ext' follows)

   count = 0

   def reorganise_row(self, row):
      self.count+=1
      temprow = row.rdict
      newrow = {}
      desc = ""
      for r in temprow:
         if temprow[r] == 'Description':
            desc = desc + r.encode('utf-8') + " * "          
         else:
            newrow[r] = temprow[r]
            
      if desc != "":
         desc = desc.strip(' * ').encode('utf-8')         
         newrow[desc] = 'Description'

      row.rdict = newrow

      return row
   
   def get_external_row(self, checksum, path):
      for row in self.externalCSV:
         if row.path == path and row.checksum == checksum:
            return self.reorganise_row(row)
      
      if row.path != path:
         sys.stderr.write("We didn't find something, path didn't match..." + row.path.encode('utf-8') + " " + path.encode('utf-8') + " " + checksum.encode('utf-8') + "\n")
         return None

      if row.checksum != checksum:
         sys.stderr.write("We didn't find something, checksum didn't match... " + row.checksum + " " + row.checksum + "\n")
         return None

   def maptoimportschema(self, externalmapping=False):
      
      if self.importschema != False:
         f = open(self.importschema, 'rb')
         
         importschemajson = f.read()

         importschema = JsonTableSchema.JSONTableSchema(importschemajson)
         importschemadict = importschema.as_dict()
         importschemaheader = importschema.as_csv_header()

         importcsv = importschemaheader + "\n"

         for filerow in self.droidlist:
         
            r = None
         
            # First, retrieve a matching row from our external CSV...
            if externalmapping is True:
               path = ""
               if 'FILE_PATH' in filerow:
                  path = self.get_path(filerow['FILE_PATH'])
               if 'MD5_HASH' in filerow:
                  hash = filerow['MD5_HASH']
               elif 'SHA1_HASH' in filerow:
                  hash = filerow['SHA1_HASH']  

               r = self.get_external_row(hash, path)
            
            # Extract year from file modified date for open and closed year
            yearopenclosed = self.retrieve_year_from_modified_date(filerow['LAST_MODIFIED'])
         
            for column in importschemadict['fields']:
               fieldtext = ""
               entry = False                              
                              
               if r is not None:                                
                  for val in r.rdict:                  
                     if column['name'] == r.rdict[val]:    
                        fieldtext = val
                        importcsv = importcsv + self.add_csv_value(fieldtext)
                        entry = True
                        break                              
                                    
               if entry != True:                                            
                  if self.config.has_option('droid mapping', column['name']):
                     droidfield = self.config.get('droid mapping', column['name'])
                     if droidfield == 'FILE_PATH':
                        dir = os.path.dirname(filerow['FILE_PATH'])
                        fieldtext = self.get_path(dir)
                     if droidfield == 'NAME':
                        fieldtext = self.get_title(filerow['NAME'])
                     if droidfield == 'MD5_HASH':
                        fieldtext = filerow['MD5_HASH']
                     if droidfield == 'SHA1_HASH':
                        fieldtext = filerow['SHA1_HASH']                     
                     if droidfield == 'LAST_MODIFIED':
                        if self.config.has_option('additional values', 'descriptiontext'):
                           fieldtext = self.config.get('additional values', 'descriptiontext') + " " + str(filerow[droidfield])
                  
                     importcsv = importcsv + self.add_csv_value(fieldtext)
                     entry = True
                  
               if self.config.has_option('static values', column['name']):
                  importcsv = importcsv + self.add_csv_value(self.config.get('static values', column['name']))
                  entry = True
               
               # If we haven't years from an external source, add them here... 
               if (column['name'] == 'Open Year') and entry != True:
                  importcsv = importcsv + self.add_csv_value(yearopenclosed)
                  entry = True
                  
               if (column['name'] == 'Close Year') and entry != True:
                  importcsv = importcsv + self.add_csv_value(yearopenclosed)
                  entry = True                  
               
               if entry == False:
                  importcsv = importcsv + self.add_csv_value("")
                  
               importcsv = importcsv + ","

            importcsv = importcsv.rstrip(',') + "\n"
         
         f.close()
      
         sys.stdout.write(importcsv)

   def readDROIDCSV(self):
      if self.droidcsv != False:
         droidcsvhandler = droidCSVHandler()
         droidlist = droidcsvhandler.readDROIDCSV(self.droidcsv)     
         droidlist = droidcsvhandler.removefolders(droidlist)
         return droidcsvhandler.removecontainercontents(droidlist)   

   def droid2archwayimport(self):
      if self.externalCSV is not None and self.droidcsv != False and self.importschema != False:
         self.droidlist = self.readDROIDCSV()
         self.maptoimportschema(True)
      elif self.droidcsv != False and self.importschema != False:
         self.droidlist = self.readDROIDCSV()
         self.maptoimportschema()
