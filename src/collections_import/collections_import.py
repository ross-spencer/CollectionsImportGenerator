""""Collections Import Generator tool."""

# pylint: disable=R0801

import argparse
import logging
import os
import sys
import tempfile
import time
from typing import Final

try:
    from import_sheet_generator import import_sheet_generator
    from json_table_schema import json_table_schema
    from schema_file import JSON_SCHEMA
except ModuleNotFoundError:
    try:
        from src.collections_import.import_sheet_generator import import_sheet_generator
        from src.collections_import.json_table_schema import json_table_schema
        from src.collections_import.schema_file import JSON_SCHEMA
    except ModuleNotFoundError:
        from collections_import.import_sheet_generator import import_sheet_generator
        from collections_import.json_table_schema import json_table_schema
        from collections_import.schema_file import JSON_SCHEMA


logger = logging.getLogger(__name__)

logging.basicConfig(
    format="%(asctime)-15s %(levelname)s :: %(filename)s:%(lineno)s:%(funcName)s() :: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level="INFO",
)

# Default to UTC time.
logging.Formatter.converter = time.gmtime


def log_encoding():
    """Diagnostics for debugging encoding issues."""

    # pylint: disable=C0301

    encoding = sys.stdout.encoding
    logger.info("console encoding: %s", encoding)
    if encoding != "utf-8":
        logger.warning("encoding '%s' may result in the script failing", encoding)
        logger.warning(
            "please try `set PYTHONIOENCODING=utf-8` (Windows) `export PYTHONIOENCODING=utf-8` (Linux)"
        )


def main():
    """Primary entry point for this script."""

    log_encoding()
    schema_filename: Final[str] = "archway-import-schema.json"
    json_schema_file = os.path.join("schema", schema_filename)
    if not os.path.exists(json_schema_file):
        # This should always be part of the package object.
        logger.error(
            "schema file does not exist: '%s' loading embedded resource",
            os.path.abspath(json_schema_file),
        )
        with tempfile.NamedTemporaryFile("w", delete=False) as schema_temp:
            schema_temp.write(JSON_SCHEMA.strip())
        json_schema_file = schema_temp.name

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

    args = parser.parse_args()

    if args.list:
        with open(json_schema_file, "r", encoding="utf-8") as import_schema_file:
            import_schema_json = import_schema_file.read()
        import_schema = json_table_schema.JSONTableSchema(import_schema_json)
        import_schema.as_csv_header()
        print("fields described in collections schema:")
        print("")
        print(", ".join(import_schema.field_names))
        sys.exit()

    # Basic import sheet with no external metadata mapping.
    if args.csv and not args.ext:
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
    if args.csv and args.ext:
        logger.info("writing full Archway import sheet with external metadata")
        import_csv = import_sheet_generator(
            droid_csv=args.csv,
            external_csv=args.ext,
            import_schema=json_schema_file,
            config=args.conf,
        )
        print(import_csv)
        sys.exit()

    parser.print_help()
    os.unlink(schema_temp.name)
    sys.exit(0)


if __name__ == "__main__":
    main()
