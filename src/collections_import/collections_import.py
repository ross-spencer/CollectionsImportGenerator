""""Collections Import Generator tool."""

import argparse
import logging
import os
import sys
import time

# pylint: disable=R0801

try:
    from ExternalCSVHandlerClass import ExternalCSVHandler
    from ImportOverviewGenerator import ImportOverviewGenerator
    from ImportSheetGenerator import ImportSheetGenerator
except ModuleNotFoundError:
    try:
        from src.collections_import.ExternalCSVHandlerClass import ExternalCSVHandler
        from src.collections_import.ImportOverviewGenerator import (
            ImportOverviewGenerator,
        )
        from src.collections_import.ImportSheetGenerator import ImportSheetGenerator
    except ModuleNotFoundError:
        from collections_import.ExternalCSVHandlerClass import ExternalCSVHandler
        from collections_import.ImportOverviewGenerator import ImportOverviewGenerator
        from collections_import.ImportSheetGenerator import ImportSheetGenerator


logger = logging.getLogger(__name__)

logging.basicConfig(
    format="%(asctime)-15s %(levelname)s :: %(filename)s:%(lineno)s:%(funcName)s() :: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level="INFO",
)

# Default to UTC time.
logging.Formatter.converter = time.gmtime


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
    jsonschema = "schema/archway-import-schema.json"

    # 	Usage: 	--csv [droid report]
    # 	Handle command line arguments for the script
    parser = argparse.ArgumentParser(
        description="Generate Archway Import Sheet and Rosetta Ingest CSV from DROID CSV Reports."
    )

    parser.add_argument(
        "--csv", help="DROID CSV to read.", default=False, required=True
    )
    parser.add_argument(
        "--over",
        "--overview",
        help="create an import overview sheet.",
        default=False,
        required=False,
        action="store_true",
    )
    parser.add_argument(
        "--ext",
        "--external",
        help="insert data from an arbitrary CSV.",
        default=False,
        required=False,
    )

    parser.add_argument(
        "--conf",
        "--config",
        help="import mapping configuration.",
        default=False,
        required=False,
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    # 	Parse arguments into namespace object to reference later in the script
    global args
    args = parser.parse_args()

    configfile = os.path.join("config", "import-mapping.cfg")
    if args.conf:
        configfile = args.conf

    # Creating an import sheet for Archway...
    if args.csv and not args.over and not args.ext:
        sys.stderr.write("Writing full Archway import sheet.\n")
        importGenerator = importsheetDROIDmapping(args.csv, jsonschema, configfile)
        createImportCSV(importGenerator)
    elif args.csv and not args.over and args.ext:
        sys.stderr.write("Writing full Archway import sheet with external metadata.\n")
        # external mapping is an involved process... it needs full knowledge of
        # two data formats, not least the import sheet layout we require...
        importGenerator = importsheetDROIDmapping(args.csv, jsonschema, configfile)
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
