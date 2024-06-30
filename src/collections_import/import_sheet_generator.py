"""Import sheet generator."""

# pylint: disable=C0301,R0913,R0914,R0912

import configparser as ConfigParser
import logging
from datetime import datetime
from typing import Final

try:
    from droid_csv_handler import DroidCSVHandler
    from external_csv_handler import ExternalCSVHandler
    from json_table_schema import json_table_schema
except ModuleNotFoundError:
    try:
        from src.collections_import.droid_csv_handler import DroidCSVHandler
        from src.collections_import.external_csv_handler import ExternalCSVHandler
        from src.collections_import.json_table_schema import json_table_schema
    except ModuleNotFoundError:
        from collections_import.droid_csv_handler import DroidCSVHandler
        from collections_import.external_csv_handler import ExternalCSVHandler
        from collections_import.json_table_schema import json_table_schema


logger = logging.getLogger(__name__)

DATE_FORMAT: Final[str] = "%Y-%m-%dT%H:%M:%S"


class ImportGenerationException(Exception):
    """Exception to raise for unrecoverable issues in this script."""


def get_droid_hash(file_row: dict) -> str:
    """Return the hash used for a given row in a DROID CSV"""

    for hash_ in ("MD5_HASH", "SHA1_HASH", "SHA256_HASH", "SHA512_HASH"):
        try:
            return file_row[hash_].lower()
        except KeyError:
            pass
    raise ImportGenerationException("hashes aren't configured in the DROID sheet")


def get_hash(file_row: dict) -> str:
    """Return the checksum value from a DROID hash field."""
    return get_droid_hash(file_row)


def retrieve_year_from_modified_date(modified_date: str) -> str:
    """Retrieve the year from the last modified date."""
    if modified_date == "":
        logger.info("Date field used to extrave 'year' is blank.")
        return ""
    try:
        return datetime.strptime(modified_date, DATE_FORMAT).year
    except ValueError as err:
        logger.info("handling unconverted data in datetime: %s", err)
        date_len: Final[int] = len("2024-06-07T13:57:03")
        return datetime.strptime(modified_date[:date_len], DATE_FORMAT).year


def add_csv_value(value):
    """Simple wrapper to generate a field for a CSV which is double-quoted."""
    return f'"{value}"'


def get_path(path, pathmask=None):
    """Retrieve a path using an optional pathmask to remove OS
    specific information, e.g. matching files across users or
    different drives.
    """
    if not pathmask:
        return path
    logger.info("using pathmask: '%s'", pathmask)
    return path.replace(pathmask, "")


def get_title(title):
    """Return a string for a record title with whitespace stripped."""
    # split once at full-stop (assumptuon 'ext' follows)
    return title.rsplit(".", 1)[0].rstrip()


def splitns(value):
    """Split namespace from a schema field entry."""
    return value.strip().split(":", 1)[1]


def map_to_collection_schema(
    import_schema,
    external_csv_row,
    droid_row,
    config,
    default_year,
    droid_only: bool = False,
):
    """Map data to a collection CSV schema."""
    importcsv = ""
    importschema = import_schema
    for column_name in importschema.field_names:
        fieldtext = ""
        entry = False
        if not droid_only and external_csv_row:
            for entry_ in external_csv_row.rdict.keys():
                field_name = external_csv_row.rdict.get(entry_)
                if column_name != field_name:
                    continue
                new_entry = ""
                if column_name != "Description":
                    new_entry = splitns(entry_)
                elif column_name == "Name":
                    new_entry = get_title(entry_)
                importcsv = f"{importcsv}{add_csv_value(new_entry)}"
                entry = True
                break
        if entry is not True:
            if config.has_option("droid mapping", column_name):
                droidfield = config.get("droid mapping", column_name)
                if droidfield == "FILE_PATH":
                    dir_ = droid_row["FILE_PATH"]
                    pathmask = config.get("additional values", "pathmask")
                    fieldtext = get_path(dir_, pathmask)
                if droidfield == "NAME":
                    fieldtext = get_title(droid_row["NAME"])
                if droidfield.endswith("_HASH"):
                    fieldtext = get_hash(file_row=droid_row)
                importcsv = importcsv + add_csv_value(fieldtext)
                entry = True
        if config.has_option("static values", column_name):
            importcsv = importcsv + add_csv_value(
                config.get("static values", column_name)
            )
            entry = True
        # If we haven't years from an external source, add them here.
        if (column_name == "Open Year") and entry is not True:
            importcsv = importcsv + add_csv_value(default_year)
            entry = True
        if (column_name == "Close Year") and entry is not True:
            importcsv = importcsv + add_csv_value(default_year)
            entry = True
        if entry is False:
            importcsv = importcsv + add_csv_value("")
        importcsv = f"{importcsv},"
    return importcsv


def get_external_row(droid_checksum, droid_path, external_csv):
    """Get a row of data from an external CSV by matching it
    against a DROID path.
    """
    for row in external_csv:
        if row.path != droid_path:
            continue
        if row.checksum.lower() != droid_checksum:
            logging.error(
                "found path: '%s' <> '%s' but checksums didn't match: %s <> %s",
                row.path,
                droid_path,
                row.checksum.lower(),
                droid_checksum,
            )
            continue
        return row
    logging.error(
        "can't find droid path in external CSV: '%s' (%s)",
        droid_path,
        droid_checksum,
    )
    return None


def _create_import_sheet(droid_csv, external_csv, import_schema, config, droid_only):
    """Wrap the creation functions.

    Given a Collections import CSV schema, data to its fields row
    by row and output a compatible CSV.

    1. DROID drives this script for digital transgers. For each
    row in a DROID report we must create an entry in the import
    sheet and pair additional data as we go.

    2. We retrieve a mapping from an external spreadsheet given a
    match on checksum and filename.

    3. Now for every field in the CSV schema file, map the entries
    per the configuration.

    4. Finally return the CSV to the console/terminal/CLI.
    """
    importschemajson = None
    with open(import_schema, "r", encoding="utf-8") as import_schema_file:
        importschemajson = import_schema_file.read()
    importschema = json_table_schema.JSONTableSchema(importschemajson)
    importschemaheader = importschema.as_csv_header()
    logger.info("mapping to: '%s' fields", len(importschema.field_names))
    importcsv = f"{importschemaheader}\n"
    # Loop over the DROID report.
    for droid_row in droid_csv:
        external_csv_row = None
        # Extract year from file modified date for open and closed
        # year for if there are no other mappings.
        default_year_open_closed = retrieve_year_from_modified_date(
            droid_row["LAST_MODIFIED"]
        )
        if external_csv:
            # we have an external CSV to map data from, retrieve each
            # row, file by file.
            droid_path = get_path(droid_row["FILE_PATH"])
            droid_hash = get_droid_hash(droid_row)
            external_csv_row = get_external_row(droid_hash, droid_path, external_csv)
        mapped_data = map_to_collection_schema(
            import_schema=importschema,
            external_csv_row=external_csv_row,
            droid_row=droid_row,
            config=config,
            default_year=default_year_open_closed,
            droid_only=droid_only,
        )
        importcsv = f"{importcsv}{mapped_data}"
        importcsv = f"{importcsv.rstrip(',')}\n"
    return importcsv


def create_import_sheet(
    droid_csv, external_csv, import_schema, config, droid_only: bool = False
):
    """Create the import sheet."""
    import_csv = _create_import_sheet(
        droid_csv,
        external_csv,
        import_schema,
        config,
        droid_only,
    )
    droid_len = len(droid_csv)
    if not droid_only:
        external_len = len(external_csv)
        logger.info(
            "COMPLETED: eexternal count: '%s', DROID count: '%s', counts equal? (%s)",
            external_len,
            droid_len,
            external_len == droid_len,
        )
        return import_csv
    logger.info("COMPLETE: DROID count: '%s'", droid_len)
    return import_csv


def create_import_csv(
    droid_csv, external_csv, import_schema, config, droid_only: bool = False
):
    """Create the import CSV."""
    if droid_only:
        return create_import_sheet(
            droid_csv=droid_csv,
            external_csv=external_csv,
            import_schema=import_schema,
            config=config,
            droid_only=True,
        )
    return create_import_sheet(
        droid_csv=droid_csv,
        external_csv=external_csv,
        import_schema=import_schema,
        config=config,
    )


def read_droid_report(droid_csv):
    """Read a DROID report for mapping."""
    droidcsvhandler = DroidCSVHandler()
    droid_list = droidcsvhandler.read_droid_csv(droid_csv)
    droid_list = droidcsvhandler.remove_folders(droid_list)
    droid_list = droidcsvhandler.remove_container_contents(droid_list)
    return droid_list


def read_config(config):
    """Read the configuration and return an error if it hasn't been
    configured correctly.
    """
    config_obj = ConfigParser.RawConfigParser()
    config_obj.read(config, encoding="utf-8")
    try:
        for section in (
            "droid mapping",
            "static values",
            "additional values",
            "external mapping config",
            "external mapping",
        ):
            config_obj.get(section, "")
    except ConfigParser.NoSectionError:
        sections = [
            "[droid mapping]",
            "[static values]",
            "[additional values]",
            "[external mapping config]",
            "[external mapping]",
        ]
        err = f"application config not setup correctly, ensure there are sections for: {', '.join(sections)}"
        raise ImportGenerationException(err) from err
    except ConfigParser.NoOptionError:
        pass
    return config_obj


def import_sheet_generator(droid_csv, external_csv, import_schema, config):
    """Primary loop for the import sheet generator."""
    config_obj = read_config(config)
    droid_csv = read_droid_report(droid_csv)
    external_data = None
    droid_only = True
    if external_csv:
        external_data = ExternalCSVHandler(config, import_schema)
        external_csv = external_data.read_external_csv(external_csv)
        droid_only = False
    import_csv = create_import_csv(
        droid_csv=droid_csv,
        external_csv=external_csv,
        import_schema=import_schema,
        config=config_obj,
        droid_only=droid_only,
    )
    return import_csv
