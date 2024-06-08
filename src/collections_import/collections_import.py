""""Collections Import Generator tool."""

# pylint: disable=R0801

import argparse
import logging
import os
import sys
import time
from typing import Final

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
    """Primary entry point for this script."""

    schema_filename: Final[str] = "archway-import-schema.json"

    json_schema_file = os.path.join("schema", schema_filename)
    if not os.path.exists(json_schema_file):
        # This should always be part of the package object.
        logger.error(
            "schema file does not exist: '%s' exiting...",
            os.path.abspath(json_schema_file),
        )
        sys.exit(1)

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

    global args
    args = parser.parse_args()

    # Basic import sheet with no external metadata mapping.
    if args.csv and not args.over and not args.ext:
        logger.info("writing full Archway import sheet")
        importGenerator = importsheetDROIDmapping(
            droidcsv=args.csv, importschema=json_schema_file, configfile=args.conf
        )
        createImportCSV(importgenerator=importGenerator)
        sys.exit()

    # Import sheet with external metadata mapping.
    if args.csv and not args.over and args.ext:
        logger.info("writing full Archway import sheet with external metadata")
        importGenerator = importsheetDROIDmapping(
            droidcsv=args.csv, importschema=json_schema_file, configfile=args.conf
        )
        handleExternalCSV(
            csv=args.ext,
            importGenerator=importGenerator,
            configfile=args.conf,
            importschema=json_schema_file,
        )
        createImportCSV(importgenerator=importGenerator)
        sys.exit()

    # Collections overview.
    if args.csv and args.over:
        logger.info("writing Archway overview sheet")
        createImportOverview(droidcsv=args.csv, configfile=args.conf)
        sys.exit()

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
