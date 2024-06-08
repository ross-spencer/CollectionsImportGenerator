""""Collections Import Generator tool."""

# pylint: disable=R0801

import argparse
import logging
import os
import sys
import time
from typing import Final

try:
    from ImportOverviewGenerator import ImportOverviewGenerator
    from ImportSheetGenerator import import_sheet_generator
    from JsonTableSchema import JsonTableSchema
except ModuleNotFoundError:
    try:
        from src.collections_import.ImportOverviewGenerator import (
            ImportOverviewGenerator,
        )
        from src.collections_import.ImportSheetGenerator import import_sheet_generator
        from src.collections_import.JsonTableSchema import JsonTableSchema
    except ModuleNotFoundError:
        from collections_import.ImportOverviewGenerator import ImportOverviewGenerator
        from collections_import.ImportSheetGenerator import import_sheet_generator
        from collections_import.JsonTableSchema import JsonTableSchema


logger = logging.getLogger(__name__)

logging.basicConfig(
    format="%(asctime)-15s %(levelname)s :: %(filename)s:%(lineno)s:%(funcName)s() :: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level="INFO",
)

# Default to UTC time.
logging.Formatter.converter = time.gmtime


def createImportOverview(droidcsv, configfile):
    createoverview = ImportOverviewGenerator(droidcsv, configfile)
    createoverview.createOverviewSheet()


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
        "--csv",
        "-c",
        help="DROID CSV to read.",
        default=False,
        required=False,
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
    parser.add_argument(
        "--list",
        "-l",
        help="list Collection CSV fields.",
        default=False,
        required=False,
        action="store_true",
    )

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)

    global args
    args = parser.parse_args()

    if args.list:
        with open(json_schema_file, "r", encoding="utf-8") as import_schema_file:
            import_schema_json = import_schema_file.read()
        import_schema = JsonTableSchema.JSONTableSchema(import_schema_json)
        import_schema.as_csv_header()
        print("fields described in collections schema:")
        print("")
        print(", ".join(import_schema.field_names))
        sys.exit()

    # Basic import sheet with no external metadata mapping.
    if args.csv and not args.over and not args.ext:
        logger.info("writing full Archway import sheet without external metadata")
        import_csv = import_sheet_generator(
            droid_csv=args.csv,
            external_csv=None,
            import_schema=json_schema_file,
            config=args.conf,
        )
        print(import_csv)
        sys.exit()

    # Import sheet with external metadata mapping.
    if args.csv and not args.over and args.ext:
        logger.info("writing full Archway import sheet with external metadata")
        import_csv = import_sheet_generator(
            droid_csv=args.csv,
            external_csv=args.ext,
            import_schema=json_schema_file,
            config=args.conf,
        )
        print(import_csv)
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
