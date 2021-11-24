# -*- coding: utf-8 -*-
import re
import sys
import unicodecsv
import ConfigParser
from os.path import exists
from datetime import datetime

from droidcsvhandlerclass import *

# Table schema code...
sys.path.append(r'JsonTableSchema/')
import JsonTableSchema


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

        self.__getconfig__()
        self.__getheaders__()

        self.__getmappingtable__()

    def __checkconfig__(self, section, name):
        if self.config.has_option(section, name):
            var = self.config.get(section, name)
            return var

    # Read the config file which contains various components for mapping data
    def __getconfig__(self):
        sys.stderr.write(
            "Mapping config being read from: " + self.configfile + "\n")
        self.config.read(self.configfile)

        # retrieve values...
        self.pathmask = self.__checkconfig__(self.mapconfig, self.pathmask)
        self.checksumcol = self.__checkconfig__(
            self.mapconfig, self.checksumcolumn)
        self.pathcol = self.__checkconfig__(self.mapconfig, self.pathcolumn)
        self.descriptiontext = self.__checkconfig__(
            self.mapping, self.desctext)

        # access our regular expression for dates...
        self.userdatepattern = self.__checkconfig__(
            self.mapconfig, self.datepattern)
        if self.userdatepattern is not None:
            self.dates = re.compile(self.userdatepattern)
        return

    # Read the import sheet headers from our CSV schema file...
    def __getheaders__(self):
        sys.stderr.write(
            "Import schema being read from: " + self.importschema + "\n")
        f = open(self.importschema, 'rb')
        importschemajson = f.read()
        importschema = JsonTableSchema.JSONTableSchema(importschemajson)
        self.importheaders = importschema.as_list()
        f.close()
        return

    # Using the CSV headers, see if there is an entry in the config file
    # for the information we're receiving in this class.
    def __getmappingtable__(self):
        for i in self.importheaders:
            if self.config.has_option(self.mapping, i):
                mapvalue = self.config.get(self.mapping, i)
                if mapvalue is not "":
                    if len(mapvalue.split(",")) > 1:
                        for j in mapvalue.split(","):
                            self.rowdict[j] = i
                            self.maphead.append(j)
                    else:
                        self.rowdict[mapvalue] = i
                        self.maphead.append(mapvalue)

        sys.stderr.write("Mapped fields ({external field: import field}): %s\n" % self.rowdict)

    # Read the external CSV we want to extract metadata from...
    def readExternalCSV(self, extcsvname):
        augmented = []  # augmented metadata
        exportlist = None
        if exists(extcsvname):
            csvhandler = genericCSVHandler()
            exportlist = csvhandler.csvaslist(extcsvname)
            # counter a blank sheet
            if len(exportlist) < 1:
                exportlist = None
            if exportlist is not None:
                for e in exportlist:
                    # we need to differentiate in case we get non-unique values
                    nscount = 0
                    row = NewRow()
                    if e[self.checksumcol] != "":
                        row.checksum = e[self.checksumcol]
                    if e[self.pathcol] != "":
                        row.path = e[self.pathcol].replace(self.pathmask, "")
                    for f in e:
                        if f in self.maphead:
                            data = e[f].strip() # remove trailing ws early
                            if re.match(self.dates, data):
                                data = self.__fixdates__(data)
                            # data is data, unless dates, but if dates, append
                            if self.rowdict[f] == 'Description':
                                if data != "":
                                    nscount += 1
                                    data = f + ": " + data
                                    data = "ns" + str(nscount) + ":" + data
                                    row.rdict[data] = self.rowdict[f]
                            else:
                                nscount += 1
                                data = "ns" + str(nscount) + ":" + data
                                row.rdict[data] = self.rowdict[f]
                    if row.checksum != "":
                        augmented.append(row)

        return self.__fixdescription__(augmented)

    def splitns(self, value):
        return value.split(':', 1)[1]

    def __fixdescription__(self, augmented_list):

        for row in augmented_list:

            newrow = {}
            desc = ""
            title = ""
            temprow = row.rdict

            # Declare these early to work with them below.
            opendate = ''
            close = ''

            for r in temprow:
                if temprow[r] == 'Description':
                    desc = desc + self.splitns(r).encode('utf-8') + ". "
                elif temprow[r] == 'Open Year':
                    opendate = self.splitns(r).encode('utf-8')
                    newrow[r] = opendate
                elif temprow[r] == 'Close Year':
                    close = self.splitns(r).encode('utf-8')
                    newrow[r] = close
                else:
                    newrow[r] = temprow[r]
            '''
            if opendate != '' and close != '':
                if int(opendate) > int(close):
                    sys.stderr.write(
                        "Dates incorrect open: " + opendate + " close: " + \
                        close + "\n")
			'''
            if desc != '' and self.descriptiontext != None:
                desc = desc + self.descriptiontext
                newrow[desc] = 'Description'

            row.rdict = newrow
            
        return augmented_list

    # Convert dates from one format to another...
    def __fixdates__(self, dates):
        if self.userdatepattern == "^[1-9]\d?\/\d{2}\/\d{4}$":
            dateobj = datetime.strptime(dates, '%d/%m/%Y')
            # return dateobj.strftime("%Y-%m-%d")
            return dateobj.strftime("%Y")
        else:
            sys.stderr.write(
                "No date handler configured for this string: " + dates)
            return dates
