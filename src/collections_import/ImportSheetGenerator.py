"""Import sheet generator."""

import configparser as ConfigParser
import logging
import sys
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


class ImportSheetGenerator:
    def __init__(self, droidcsv, importschema, configfile):
        self.externalCSV = None
        self.config = ConfigParser.RawConfigParser()
        if configfile is not False and configfile is not None:
            self.config.read(configfile)
            self.pathmask = self.config.get("additional values", "pathmask")
        self.droidcsv = droidcsv
        self.importschema = importschema

    def setExternalCSV(self, externalCSV):
        if externalCSV is not None:
            self.externalCSV = externalCSV
        else:
            self.externalCSV = None

    def retrieve_year_from_modified_date(self, modified_date: str) -> str:
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

    def add_csv_value(self, value):
        field = ""
        if type(value) is int:  # TODO: probably a better way to do this (type-agnostic)
            field = f'"{value}"'
        else:
            field = f'"{value}"'
        return field

    def get_path(self, path):
        return path.replace(self.pathmask, "")

    def get_title(self, title):
        # split once at full-stop (assumptuon 'ext' follows)
        return title.rsplit(".", 1)[0].rstrip()

    count = 0

    def splitns(self, value):
        return value.split(":", 1)[1]

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
                    row.checksum,
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

    def maptoimportschema(self, externalmapping=False):
        if self.importschema is not False:
            f = open(self.importschema, "rb")

            importschemajson = f.read()

            importschema = JsonTableSchema.JSONTableSchema(importschemajson)
            importschemadict = importschema.as_dict()
            importschemaheader = importschema.as_csv_header()

            importcsv = importschemaheader + "\n"

            for filerow in self.droidlist:
                r = None

                # First, retrieve a matching row from our external CSV...
                if externalmapping is True:
                    droid_path = ""
                    # filerow is a DROID row again so let's use generic
                    # DROID functions here.
                    if "FILE_PATH" in filerow:
                        droid_path = self.get_path(filerow["FILE_PATH"])
                    droid_hash = get_droid_hash(filerow)
                    r = self.get_external_row(droid_hash, droid_path)

                # Extract year from file modified date for open and closed year
                yearopenclosed = self.retrieve_year_from_modified_date(
                    filerow["LAST_MODIFIED"]
                )

                for column in importschemadict["fields"]:
                    fieldtext = ""
                    entry = False

                    if r is not None:
                        for val in r.rdict:
                            if column["name"] == r.rdict[val]:
                                if column["name"] != "Description":
                                    val = self.splitns(val)
                                fieldtext = val
                                if column["name"] == "Title":
                                    fieldtext = self.get_title(fieldtext)
                                importcsv = importcsv + self.add_csv_value(fieldtext)
                                entry = True
                                break

                    if entry is not True:
                        if self.config.has_option("droid mapping", column["name"]):
                            droidfield = self.config.get(
                                "droid mapping", column["name"]
                            )
                            if droidfield == "FILE_PATH":
                                dir = os.path.dirname(filerow["FILE_PATH"])
                                fieldtext = self.get_path(dir)
                            if droidfield == "NAME":
                                fieldtext = self.get_title(filerow["NAME"])
                            if droidfield.endswith("_HASH"):
                                fieldtext = get_hash(file_row=filerow)
                            if droidfield == "LAST_MODIFIED":
                                if self.config.has_option(
                                    "additional values", "descriptiontext"
                                ):
                                    fieldtext = (
                                        self.config.get(
                                            "additional values", "descriptiontext"
                                        )
                                        + " "
                                        + str(filerow[droidfield])
                                    )

                            importcsv = importcsv + self.add_csv_value(fieldtext)
                            entry = True

                    if self.config.has_option("static values", column["name"]):
                        importcsv = importcsv + self.add_csv_value(
                            self.config.get("static values", column["name"])
                        )
                        entry = True

                    # If we haven't years from an external source, add them
                    # here...
                    if (column["name"] == "Open Year") and entry is not True:
                        importcsv = importcsv + self.add_csv_value(yearopenclosed)
                        entry = True

                    if (column["name"] == "Close Year") and entry is not True:
                        importcsv = importcsv + self.add_csv_value(yearopenclosed)
                        entry = True

                    if entry is False:
                        importcsv = importcsv + self.add_csv_value("")

                    importcsv = importcsv + ","

                importcsv = importcsv.rstrip(",") + "\n"

            f.close()

            sys.stdout.write(importcsv)

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
            self.maptoimportschema(True)
            sys.stderr.write(
                "External count: "
                + str(len(self.externalCSV))
                + " DROID Count: "
                + str(len(self.droidlist))
                + "\n"
            )
        elif self.droidcsv is not False and self.importschema is not False:
            self.droidlist = self.readDROIDCSV()
            self.maptoimportschema()
