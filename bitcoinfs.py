#!/usr/bin/env python3
"""
BitcoinFS main script
"""

from fusepy import FUSE, Operations, LoggingMixIn
from collections import defaultdict
from errno import ENOENT
from stat import S_IFDIR, S_IFLNK, S_IFREG
from sys import argv, exit
from time import time
import logging
from bitcoincmd import *
import os
import traceback
import subprocess as sb
import binascii
import json
import uuid

def genrndf():
  return "/tmp/"+str(uuid.uuid4())


class BitcoinFS(LoggingMixIn, Operations):
    """In memory filesystem. Supports only one level of files."""
    
    def __init__(self,data):
        self.bsvtx = data
        self.files = {}
        self.data = defaultdict(bytearray)
        self.fd = 0
        now = time()
        self.files['/'] = dict(st_mode=(S_IFDIR | 0o755), st_ctime=now,
            st_mtime=now, st_atime=now, st_nlink=2)
        for fname in data:
            chunks = []
            for txid in data[fname]:
                chunks.append(txid2boptreturn(txid))
            chunks = b''.join(chunks)
            self.files["/"+fname] = dict(st_mode=(S_IFREG | 0o600), st_nlink=1,st_size=len(chunks), st_ctime=time(), st_mtime=time(), st_atime=time())
            self.data["/"+fname] = bytearray(chunks)


    def chmod(self, path, mode): 
        self.files[path]['st_mode'] &= 0o770000
        self.files[path]['st_mode'] |= mode
        return 0
    def chown(self, path, uid, gid):
        self.files[path]['st_uid'] = uid
        self.files[path]['st_gid'] = gid
    
    def create(self, path, mode):
        self.files[path] = dict(st_mode=(S_IFREG | mode), st_nlink=1,
            st_size=0, st_ctime=time(), st_mtime=time(), st_atime=time())
        self.fd += 1
        return self.fd
    
    def getattr(self, path, fh=None):
        if path not in self.files:
            raise OSError(ENOENT, '')
        st = self.files[path]
        return st
    
    def mkdir(self, path, mode):
        self.files[path] = dict(st_mode=(S_IFDIR | mode), st_nlink=2,
                st_size=0, st_ctime=time(), st_mtime=time(), st_atime=time())
        self.files['/']['st_nlink'] += 1
    
    def open(self, path, flags):
        self.fd += 1
        return self.fd
    
    def read(self, path, size, offset, fh):
        return bytes(self.data[path][offset:offset + size])
    
    def readdir(self, path, fh):
        return ['.', '..'] + [x[1:] for x in self.files if x != '/']
    
    def readlink(self, path):
        return self.data[path].decode('utf-8')
    
    def removexattr(self, path, name):
        attrs = self.files[path].get('attrs', {})
        try:
            del attrs[name]
        except KeyError:
            pass        # Should return ENOATTR
    
    def rename(self, old, new):
        self.files[new] = self.files.pop(old)
    
    def rmdir(self, path):
        self.files.pop(path)
        self.files['/']['st_nlink'] -= 1
    
    def statfs(self, path):
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)
    
    def symlink(self, target, source):
        source = source.encode('utf-8')
        self.files[target] = dict(st_mode=(S_IFLNK | 0o777), st_nlink=1,
            st_size=len(source))
        self.data[target] = bytearray(source)
    
    def truncate(self, path, length, fh=None):
        del self.data[path][length:]
        self.files[path]['st_size'] = length
    
    def unlink(self, path):
        self.files.pop(path)
    
    def utimens(self, path, times=None):
        now = time()
        atime, mtime = times if times else (now, now)
        self.files[path]['st_atime'] = atime
        self.files[path]['st_mtime'] = mtime

#read only for now    
#    def write(self, path, data, offset, fh):
#        del self.data[path][offset:]
#        self.data[path].extend(data)
#        self.files[path]['st_size'] = len(self.data[path])
#        return len(data)


def parseconf(fname):
    lines = [ item.strip() for item in open(fname).readlines() if not "#" in item ]
    res = {}
    for line in lines:
        tk = line.split(" ")
        if len(tk) < 2:
          continue
        fname = tk[0]
        txid = tk[1]
        if not fname in res:
            res[fname] = []
        res[fname].append(txid)
    return res


if __name__ == "__main__":
    conf1 = "./bitcoinfs.conf"
    conf2 = "~/.bitcoinfs.conf"
    conf3 = getrndf()
    if len(argv) < 2:
        print('usage: %s <mountpoint> <filelist txid>' % argv[0])
        exit(1)
    if argv[1] in ["-h","--help"]:
        print('usage: %s <mountpoint> <filelist txid>\nNeeds the bitcoinfs.conf in the same folder as executable or as ~/.bitcoinfs.conf in home folder, alternatively we can fetch the file list directly from the blockchain using the txid\n' % (argv[0]))
    if len(argv) == 3:
      confd = txid2boptreturn(argv[2])
      f = open(conf3,"wb")
      f.write(confd)
      f.close()
      conf = conf3
    elif os.path.isfile(conf1):
        conf=conf1
    elif os.path.isfile(conf2):
        conf=conf2
    else:
        print('No configuration file found')
        exit()
    try:
       data = parseconf(conf)
       logging.getLogger().setLevel(logging.DEBUG)
       fuse = FUSE(BitcoinFS(data), argv[1], foreground=True)
    except:
       traceback.print_exc() 


