# -*- coding: utf-8 -*-
import sys
import argparse
from libs.ImportOverviewGenerator import ImportOverviewGenerator
from libs.ImportSheetGenerator import ImportSheetGenerator
from libs.ExternalCSVHandlerClass import ExternalCSVHandler


def handleExternalCSV(csv, importGenerator, configfile, importschema):
    ex = ExternalCSVHandler(configfile, importschema)
    externalCSV = ex.readExternalCSV(csv)
    importGenerator.setExternalCSV(externalCSV)
    return


def createImportOverview(droidcsv, configfile):
    createoverview = ImportOverviewGenerator(droidcsv, configfile)
    createoverview.createOverviewSheet()


def importsheetDROIDmapping(droidcsv, importschema, configfile):
    importgenerator = ImportSheetGenerator(droidcsv, importschema, configfile)
    return importgenerator


def createImportCSV(importgenerator):
    importgenerator.droid2archwayimport()


def main():

    configfile = "config/import-mapping.cfg"
    jsonschema = "schema/archway-import-schema.json"

    #	Usage: 	--csv [droid report]
    #	Handle command line arguments for the script
    parser = argparse.ArgumentParser(
        description='Generate Archway Import Sheet and Rosetta Ingest CSV from DROID CSV Reports.')

    parser.add_argument(
        '--csv', help='Single DROID CSV to read.', default=False, required=True)
    parser.add_argument(
        '--over', '--overview', help='Create an import overview sheet.',
                        default=False, required=False, action="store_true")
    parser.add_argument(
        '--ext', '--external', help='Insert data from an arbitrary CSV.', default=False, required=False)

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    #	Parse arguments into namespace object to reference later in the script
    global args
    args = parser.parse_args()

    # Creating an import sheet for Archway...
    if args.csv and not args.over and not args.ext:
        sys.stderr.write("Writing full Archway import sheet.\n")
        importGenerator = importsheetDROIDmapping(
            args.csv, jsonschema, configfile)
        createImportCSV(importGenerator)
    elif args.csv and not args.over and args.ext:
        sys.stderr.write(
            "Writing full Archway import sheet with external metadata.\n")
        # external mapping is an involved process... it needs full knowledge of
        # two data formats, not least the import sheet layout we require...
        importGenerator = importsheetDROIDmapping(
            args.csv, jsonschema, configfile)
        handleExternalCSV(args.ext, importGenerator, configfile, jsonschema)
        createImportCSV(importGenerator)
    # Creating a cover sheet for Archway...
    elif args.csv and args.over:
        sys.stderr.write("Writing Archway overview sheet.\n")
        createImportOverview(args.csv, configfile)
    # We're not doing anything sensible...
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
