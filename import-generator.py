# -*- coding: utf-8 -*-

import sys
import argparse
from libs.ImportOverviewGenerator import ImportOverviewGenerator
from libs.ImportSheetGenerator import ImportSheetGenerator
         
def createImportOverview(droidcsv, configfile):
   createoverview = ImportOverviewGenerator(droidcsv, configfile)
   createoverview.createOverviewSheet()

def importsheetDROIDmapping(droidcsv, importschema, configfile):
   importgenerator = ImportSheetGenerator(droidcsv, importschema, configfile)
   importgenerator.droid2archwayimport()

def main():

   configfile = "config/import-mapping.cfg"
   jsonschema = "schema/archway-import-schema.json"

   #	Usage: 	--csv [droid report]
   #	Handle command line arguments for the script
   parser = argparse.ArgumentParser(description='Generate Archway Import Sheet and Rosetta Ingest CSV from DROID CSV Reports.')

   parser.add_argument('--csv', help='Single DROID CSV to read.', default=False, required=False)
   parser.add_argument('--over','--overview', help='Create an import overview sheet.', default=False, required=False, action="store_true")

   if len(sys.argv)==1:
      parser.print_help()
      sys.exit(1)

   #	Parse arguments into namespace object to reference later in the script
   global args
   args = parser.parse_args()
       
   # Creating an import sheet for Archway...
   if args.csv and not args.over:
      importsheetDROIDmapping(args.csv, jsonschema, configfile)
   # Creating a cover sheet for Archway...
   elif args.csv and args.over :
      createImportOverview(args.csv, configfile)
   # We're not doing anything sensible...
   else:
      parser.print_help()
      sys.exit(1)

if __name__ == "__main__":
   main()
