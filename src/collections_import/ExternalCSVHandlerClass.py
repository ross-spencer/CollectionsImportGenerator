"""External CSV handler."""

import configparser as ConfigParser
import logging
import re
import sys
from datetime import datetime
from os.path import exists

# pylint: disable=R0801

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


class NewRow:
    checksum = ""
    path = ""
    rdict = {}

    def __init__(self):
        self.rdict = {}  # shares memory if not initialized every call?


class ExternalCSVHandler:
    # place to store cfg loc
    configfile = False

    # config section in cfg
    mapconfig = "external mapping config"

    # mapping section in cfg
    mapping = "external mapping"

    # data we want to read from the config file...
    pathcolumn = "PathColumn"
    checksumcolumn = "ChecksumColumn"
    pathmask = "Mask"
    datepattern = "Date Pattern"
    desctext = "descriptiontext"

    rowdict = {}
    maphead = []

    def __init__(self, configfile, importschema):
        self.config = ConfigParser.RawConfigParser()

        self.configfile = configfile
        self.importschema = importschema

        self.get_import_configuration()
        self.get_import_table_headers()

        self.get_mappings()

    def __checkconfig__(self, section, name):
        if self.config.has_option(section, name):
            var = self.config.get(section, name)
            return var

    def get_import_configuration(self):
        """Read the import config file which describes the mapping
        we need to convert an external CSV into an import sheet.
        """
        logger.info("mapping config being read from: '%s'", self.configfile)
        self.config.read(self.configfile)
        self.pathmask = self.__checkconfig__(self.mapconfig, self.pathmask)
        self.checksumcol = self.__checkconfig__(self.mapconfig, self.checksumcolumn)
        self.pathcol = self.__checkconfig__(self.mapconfig, self.pathcolumn)
        self.descriptiontext = self.__checkconfig__(self.mapping, self.desctext)
        self.userdatepattern = self.__checkconfig__(self.mapconfig, self.datepattern)
        if self.userdatepattern is not None:
            self.dates = re.compile(self.userdatepattern)
        return

    # Read the import sheet headers from our CSV schema file...
    def get_import_table_headers(self):
        """Read the import table schema headers for our CSV file from
        the import schema declaration.
        """
        logging.info("import table schema being read from: %s", self.importschema)
        with open(self.importschema, "rb") as schema:
            importschemajson = schema.read()
            importschema = JsonTableSchema.JSONTableSchema(importschemajson)
            self.import_schema_headers = importschema.field_names
        return

    def get_mappings(self):
        """TODO... map something...
        Using the CSV headers, see if there is an entry in the config file
        for the information we're receiving in this class.
        """
        for header in self.import_schema_headers:
            if not self.config.has_option(self.mapping, header):
                continue
            mapvalue = self.config.get(self.mapping, header)
            if mapvalue == "":
                continue
            if len(mapvalue.split(",")) > 1:
                for value in mapvalue.split(","):
                    self.rowdict[value] = header
                    self.maphead.append(value)
            else:
                self.rowdict[mapvalue] = header
                self.maphead.append(mapvalue)

        logger.info("mapped fields ({external field: import field}): %s", self.rowdict)

    def readExternalCSV(self, extcsvname):
        """Read the external CSV we want to extract metadata from..."""
        augmented = []  # augmented metadata
        exportlist = None
        if exists(extcsvname):
            csvhandler = genericCSVHandler()
            exportlist = csvhandler.csvaslist(extcsvname)
            # counter a blank sheet
            if len(exportlist) < 1:
                exportlist = None
            if exportlist is not None:
                for external_row in exportlist:
                    # we need to differentiate in case we get non-unique values
                    nscount = 0
                    row = NewRow()
                    if external_row[self.checksumcol] != "":
                        row.checksum = external_row[self.checksumcol]
                    if external_row[self.pathcol] != "":
                        row.path = external_row[self.pathcol].replace(self.pathmask, "")
                    for field in external_row:
                        if field in self.maphead:
                            data = external_row[field].strip()
                            if re.match(self.dates, data):
                                data = self.__fixdates__(data)
                            if self.rowdict[field] == "Description":
                                if data != "":
                                    nscount += 1
                                    data = field + ": " + data
                                    data = "ns" + str(nscount) + ":" + data
                                    row.rdict[data] = self.rowdict[f]
                            else:
                                nscount += 1
                                data = f"ns{nscount}:{data}"
                                row.rdict[data] = self.rowdict[field]
                    if row.checksum != "":
                        augmented.append(row)

        return self.__fixdescription__(augmented)

    def splitns(self, value):
        return value.split(":", 1)[1]

    def __fixdescription__(self, augmented_list):
        for row in augmented_list:
            newrow = {}
            desc = ""
            temprow = row.rdict

            # Declare these early to work with them below.
            opendate = ""
            close = ""

            for r in temprow:
                if temprow[r] == "Description":
                    desc = desc + self.splitns(r).encode("utf-8") + ". "
                elif temprow[r] == "Open Year":
                    opendate = self.splitns(r).encode("utf-8")
                    newrow[r] = opendate
                elif temprow[r] == "Close Year":
                    close = self.splitns(r).encode("utf-8")
                    newrow[r] = close
                else:
                    newrow[r] = temprow[r]
            """
            if opendate != '' and close != '':
                if int(opendate) > int(close):
                    sys.stderr.write(
                        "Dates incorrect open: " + opendate + " close: " + \
                        close + "\n")
			"""
            if desc != "" and self.descriptiontext is not None:
                desc = desc + self.descriptiontext
                newrow[desc] = "Description"

            row.rdict = newrow

        return augmented_list

    # Convert dates from one format to another...
    def __fixdates__(self, dates):
        if self.userdatepattern == "^[1-9]\d?\/\d{2}\/\d{4}$":
            dateobj = datetime.strptime(dates, "%d/%m/%Y")
            # return dateobj.strftime("%Y-%m-%d")
            return dateobj.strftime("%Y")
        else:
            sys.stderr.write("No date handler configured for this string: " + dates)
            return dates
