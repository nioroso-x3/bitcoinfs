import os
import sys
import time
import netrc
import logging
from urllib.parse import quote, unquote
from email.utils import parsedate
from html.parser import HTMLParser
from stat import S_IFDIR, S_IFREG
from errno import EIO, ENOENT, EBADF, EHOSTUNREACH
from multiprocessing import dummy as mp

import fuse
import requests


logger = logging.getLogger(__name__)


class Config:
    mountpoint = None
    timeout = None
    verify = None
    system_ca = None
    poolsize = 15


class Path:

    def __init__(self, parent, name):
        self.parent = parent
        self.name = name
        self.initialized = False

    def buildUrl(self):
        return self.parent.buildUrl() + "/" + quote(self.name.encode('utf-8'))

    def getSession(self):
        return self.parent.getSession()

    def getAttr(self):
        raise fuse.FuseOSError(ENOENT)

    @classmethod
    def fromPath(clazz, parent, pathElement):
        if type(pathElement) == bytes:
            pathElement = pathElement.decode('utf-8')
        p = clazz(parent, unquote(pathElement))
        logger.info("created {} '{}' referencing {}".format(
            clazz.__name__, p.name, p.buildUrl()))
        return p


class File(Path):

    def __init__(self, parent, name):
        super().__init__(parent, name)
        self.lastModified = None
        self.size = None
        self.mode = 0o444

    def init(self):
        url = self.buildUrl()
        logger.info("File url={} name={}".format(url, self.name))
        r = self.getSession().head(url, timeout=Config.timeout,
                                   allow_redirects=True)
        r.close()
        if r.status_code >= 400 and r.status_code <= 499:
            self.size = 0
            self.mode = 0o000
            self.initialized = True
            self.lastModified = 0
            return
        elif r.status_code != 200:
            error = "Status code != 200 for {}: {}".format(url, r.status_code)
            raise Exception(error)
        self.size = int(r.headers['content-length'])
        self.lastModified = time.mktime(parsedate(r.headers['last-modified']))

        logger.info("File initialized url={} name={}".format(url, self.name))
        self.initialized = True

    def get(self, size, offset):
        if not self.initialized:
            self.init()
        url = self.buildUrl()
        bytesRange = '{}-{}'.format(offset, min(self.size, offset + size - 1))
        headers = {'range': 'bytes=' + bytesRange}
        logger.info("File.get url={} range={}".format(url, bytesRange))
        r = self.getSession().get(url, headers=headers, timeout=Config.timeout)
        r.close()
        if r.status_code == 200 or r.status_code == 206:
            d = r.content
            logger.info("Received {} bytes".format(len(d)))
            if len(d) > size:
                errormsg = "size {} > than expected {}".format(len(d), size)
                logger.error(errormsg)
                raise fuse.FuseOSError(EIO)
            return d
        else:
            raise fuse.FuseOSError(EIO)

    def getAttr(self):
        if not self.initialized:
            self.init()
        t = self.lastModified
        return dict(st_mode=(S_IFREG | self.mode), st_nlink=1,
                    st_size=self.size,
                    st_ctime=t, st_mtime=t, st_atime=t,
                    st_uid=os.getuid(), st_gid=os.getgid())


class Directory(Path):

    def __init__(self, parent, name):
        super().__init__(parent, name)
        self.entries = {}
        self.mode = 0o555

    def init(self):
        url = self.buildUrl() + "/"
        logger.info("Directory url={} name={}".format(url, self.name))
        r = self.getSession().get(url, stream=True, timeout=Config.timeout)
        if r.status_code >= 400 and r.status_code <= 499:
            self.mode = 0o000
            logger.info("Directory is 4xx {}".format(url))
            r.close()
            self.initialized = True
            return
        elif r.status_code != 200:
            raise Exception("Status code not 200 for {}: {}".format(
                url, r.status_code))

        if "text/html" not in r.headers['content-type']:
            raise Exception("Is not text/html: {}".format(url))

        parser = RelativeLinkCollector(self)
        for line in r.iter_content(decode_unicode=True):
            parser.feed(line)
            self.entries.update(parser.entries)
            parser.entries.clear()
        parser.close()
        self.entries.update(parser.entries)
        r.close()

        files = filter(lambda obj: isinstance(obj, File),
                       self.entries.values())
        pool = mp.Pool(Config.poolsize)
        pool.map(lambda it: it.init(), files)

        logger.info("Diretory loaded {}".format(url))
        self.initialized = True

    def getAttr(self):
        t = time.time()
        nentries = 1
        if self.initialized:
            nentries += len(self.entries)
        return dict(st_mode=(S_IFDIR | self.mode), st_nlink=nentries,
                    st_ctime=t, st_mtime=t, st_atime=t,
                    st_uid=os.getuid(), st_gid=os.getgid())


class Server(Directory):

    def __init__(self, parent, name):
        super().__init__(parent, name)
        self.session = requests.Session()
        self.session.allow_redirects = True
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=Config.poolsize, pool_maxsize=Config.poolsize)
        if Config.verify == "default":
            pass
        elif Config.verify == "system":
            self.session.verify = Config.system_ca
        elif Config.verify == "none":
            logger.warning("SSL Verification disabled!")
            self.session.verify = False
        else:
            raise SystemExit("Invalid value for ssl verification")

    def getSession(self):
        return self.session

    def buildUrl(self):
        return self.parent.buildUrl() + "/" + self.name


class Schema(Directory):

    def __init__(self, parent, name):
        super().__init__(parent, name)
        self.initialized = True

    def buildUrl(self):
        return self.name + ":/"


class Root(Directory):

    def __init__(self):
        super().__init__(None, "")
        self.initialized = True

    def buildUrl(self):
        return ""


class RelativeLinkCollector(HTMLParser):

    def __init__(self, parent):
        super().__init__(convert_charrefs=True)
        self.parent = parent
        self.entries = {}

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attrs = dict(attrs)
            if "href" in attrs:
                href = attrs["href"]
                if "/" in href[:-1] or href[0] == "." \
                        or href[0] == "?" or href == "/":
                    return

                if href[-1:] == "/":
                    # ends with / => directory
                    d = Directory.fromPath(self.parent, href[:-1])
                    self.entries[unquote(href[:-1])] = d
                else:
                    f = File.fromPath(self.parent, href)
                    self.entries[unquote(href)] = f


class Httpfs(fuse.LoggingMixIn, fuse.Operations):
    """A read only http/https/ftp filesystem using python-requests."""

    def __init__(self):
        self.root = Root()

        https = Schema(self.root, 'https')
        https.entries = dict(self._getDefaultEntries(https))
        http = Schema(self.root, 'http')
        http.entries = dict(self._getDefaultEntries(http))

        self.root.entries = {'http': http, 'https': https}

    def _getDefaultEntries(self, parent):
        try:
            for machine in netrc.netrc().hosts.keys():
                yield (machine, Server(parent, machine))
        except IOError as e:
            logger.warning("No .netrc file found, no default machines")

    def getattr(self, path, fh=None):
        logger.debug("getattr path={}".format(path))
        try:
            entry = self._getPath(path)
            if entry:
                return entry.getAttr()
        except Exception as e:
            logger.exception("Error in getattr(%s)", path)
            raise fuse.FuseOSError(EHOSTUNREACH)
        raise fuse.FuseOSError(ENOENT)

    def _getPath(self, path):
        """ map path to self.root tree
        a path is build like /<schema>/<server hostname>/<http-path>"""
        logger.debug("getPath path={}".format(path))
        if path == "/":
            return self.root

        if path[-1] == "/":
            path = path[:-1]

        schema, *p = path[1:].split("/")
        if schema not in self.root.entries:
            logger.debug("schema %s not in root.entries", schema)
            return None
        prevEntry = self.root.entries[schema]
        if p == []:
            return prevEntry

        server, *p = p
        if server not in prevEntry.entries:
            # create server if not exists
            prevEntry.entries[server] = Server.fromPath(prevEntry, server)
        prevEntry = prevEntry.entries[server]
        if p == []:
            return prevEntry

        *pathElements, lastElement = p
        for pathElement in pathElements:
            if pathElement not in prevEntry.entries:
                d = Directory.fromPath(prevEntry, pathElement)
                prevEntry.entries[pathElement] = d
            prevEntry = prevEntry.entries[pathElement]

        if lastElement not in prevEntry.entries:
            if not prevEntry.initialized:
                prevEntry.init()
            if lastElement not in prevEntry.entries:
                # the server don't return it, then just create it
                # assuming its an directory, if a HEAD is successful
                d = Directory.fromPath(prevEntry, lastElement)
                url = d.buildUrl()
                r = d.getSession().head(url, timeout=Config.timeout,
                                        allow_redirects=True)
                if r.status_code == 200:
                    logger.info("Create directory for path: {} "
                                "at: {}".format(path, url))
                    prevEntry.entries[lastElement] = d
                else:
                    logger.info("Path not found ({}): {} for {}".format(
                        r.status_code, path, url))
                    return None
        return prevEntry.entries[lastElement]

    def readdir(self, path, fh):
        try:
            logger.debug("readdir path=%s", path)
            entry = self._getPath(path)
            if not entry:
                raise fuse.FuseOSError(EBADF)
            if not entry.initialized:
                entry.init()
            return [
                (".", entry.getAttr(), 0),
                ("..", (entry.parent and entry.parent.getAttr() or None), 0)
                ] + [
                (it.name, it.getAttr(), 0) for it in entry.entries.values()
                ]
        except Exception as e:
            logger.exception("Error in readdir(%s)", path)
            raise fuse.FuseOSError(EIO)

    def read(self, path, size, offset, fh):
        entry = self._getPath(path)
        if isinstance(entry, File):
            return entry.get(size, offset)
        else:
            raise fuse.FuseOSError(EIO)

