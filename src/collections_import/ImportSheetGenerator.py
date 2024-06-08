"""Import sheet generator."""

import configparser as ConfigParser
import logging
from datetime import datetime
from typing import Final

try:
    from droidcsvhandlerclass import *
    from JsonTableSchema import JsonTableSchema
except ModuleNotFoundError:
    try:
        from src.collections_import.droidcsvhandlerclass import *
        from src.collections_import.JsonTableSchema import JsonTableSchema
    except ModuleNotFoundError:
        from collections_import.droidcsvhandlerclass import *
        from collections_import.JsonTableSchema import JsonTableSchema


logger = logging.getLogger(__name__)

DATE_FORMAT: Final[str] = "%Y-%m-%dT%H:%M:%S"


class ImportGenerationException(Exception):
    """Exception to raise for unrecoverable issues in this script."""


def get_droid_hash(file_row: dict) -> str:
    """Return the hash used for a given row in a DROID CSV"""

    for hash in ("MD5_HASH", "SHA1_HASH", "SHA256_HASH", "SHA512_HASH"):
        try:
            return file_row[hash].lower()
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
    field = ""
    if type(value) is int:  # TODO: probably a better way to do this (type-agnostic)
        field = f'"{value}"'
    else:
        field = f'"{value}"'
    return field


def get_path(path, pathmask=None):
    """Retrieve a path using an optional pathmask to remove OS
    specific information, e.g. matching files across users or
    different drives.
    """
    if not pathmask:
        return
    logger.info("using pathmask: '%s'", pathmask)
    return path.replace(pathmask, "")


def get_title(title):
    # split once at full-stop (assumptuon 'ext' follows)
    return title.rsplit(".", 1)[0].rstrip()


def splitns(value):
    """Split namespace from a schema field entry."""
    return value.strip().split(":", 1)[1]


def map_to_collection_schema(
    import_schema, external_csv_row, droid_row, config, default_year
):
    """Map data to a collection CSV schema."""
    importcsv = ""
    importschema = import_schema
    for column_name in importschema.field_names:
        fieldtext = ""
        entry = False
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
                    dir = os.path.dirname(droid_row["FILE_PATH"])
                    pathmask = config.get("additional values", "pathmask")
                    fieldtext = get_path(dir, pathmask)
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


class ImportSheetGenerator:
    def __init__(self, droidcsv, importschema, configfile):
        self.externalCSV = None
        self.config = ConfigParser.RawConfigParser()
        if configfile is not False and configfile is not None:
            self.config.read(configfile)
        self.droidcsv = droidcsv
        self.importschema = importschema
        self.pathmask = None

    def setExternalCSV(self, externalCSV):
        if externalCSV is not None:
            self.externalCSV = externalCSV
        else:
            self.externalCSV = None

    def add_csv_value(self, value):
        field = ""
        if type(value) is int:  # TODO: probably a better way to do this (type-agnostic)
            field = f'"{value}"'
        else:
            field = f'"{value}"'
        return field

    def get_path(self, path):
        """Retrieve a path using an optional pathmask to remove OS
        specific information, e.g. matching files across users or
        different drives.
        """
        if not self.pathmask:
            return path
        logger.info("using pathmask: '%s'", self.pathmask)
        return path.replace(self.pathmask, "")

    def get_title(self, title):
        # split once at full-stop (assumptuon 'ext' follows)
        return title.rsplit(".", 1)[0].rstrip()

    def splitns(self, value):
        """Split namespace from a schema field entry."""
        return value.strip().split(":", 1)[1]

    def get_external_row(self, droid_checksum, droid_path):
        """Get a row of data from an external CSV by matching it
        against a DROID path.
        """
        for row in self.externalCSV:
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

    def map_to_import_schema(self, externalmapping: bool = False):
        """Given a Collections import CSV schema, data to its fields row
        by row and output a compatible CSV.

        1. DROID drives this script for digital transgers. For each
        row in a DROID report we must create an entry in the import
        sheet and pair additional data as we go.

        2. We retieve a mapping from an external spreadsheet given a
        match on checksum and filename.

        3. Now for every field in the CSV schema file, map the entries
        per the configuration.

        4. Finally return the CSV to the console/terminal/CLI.
        """
        importschemajson = None
        with open(self.importschema, "r", encoding="utf-8") as import_schema_file:
            importschemajson = import_schema_file.read()
        importschema = JsonTableSchema.JSONTableSchema(importschemajson)
        importschemaheader = importschema.as_csv_header()
        logger.info("mapping to: '%s' fields", len(importschema.field_names))
        importcsv = f"{importschemaheader}\n"
        # Loop over the DROID report.
        for droid_row in self.droidlist:
            external_csv_row = None
            # Extract year from file modified date for open and closed
            # year for if there are no other mappings.
            default_year_open_closed = retrieve_year_from_modified_date(
                droid_row["LAST_MODIFIED"]
            )
            if externalmapping:
                # we have an external CSV to map data from, retrieve each
                # row, file by file.
                droid_path = self.get_path(droid_row["FILE_PATH"])
                droid_hash = get_droid_hash(droid_row)
                external_csv_row = self.get_external_row(droid_hash, droid_path)
            mapped_data = map_to_collection_schema(
                import_schema=importschema,
                external_csv_row=external_csv_row,
                droid_row=droid_row,
                config=self.config,
                default_year=default_year_open_closed,
            )
            importcsv = f"{importcsv}{mapped_data}"
            importcsv = f"{importcsv.rstrip(',')}\n"
        print(importcsv)

    def readDROIDCSV(self):
        if self.droidcsv is not False:
            droidcsvhandler = droidCSVHandler()
            droidlist = droidcsvhandler.readDROIDCSV(self.droidcsv)
            droidlist = droidcsvhandler.removefolders(droidlist)
            return droidcsvhandler.removecontainercontents(droidlist)

    def droid2archwayimport(self):
        if (
            self.externalCSV is not None
            and self.droidcsv is not False
            and self.importschema is not False
        ):
            self.droidlist = self.readDROIDCSV()
            self.map_to_import_schema(True)
            external_len = len(self.externalCSV)
            droid_len = len(self.droidlist)
            logger.info(
                "eexternal count: '%s', DROID count: '%s', counts equal? (%s)",
                external_len,
                droid_len,
                external_len == droid_len,
            )
        elif self.droidcsv is not False and self.importschema is not False:
            self.droidlist = self.readDROIDCSV()
            self.maptoimportschema()
