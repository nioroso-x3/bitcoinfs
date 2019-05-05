# bitcoinfs
FUSE interface for blockchain file storage

Requires python3 with the fusepy and requests libraries.
bitcoin-cli is required to use the file upload scripts

* Installing requeriments:
In Ubuntu Linux 18.04:
apt-get install python3-fusepy python3-requests

In OSX:
Not tested due to no available machine, but it should work with MacFUSE installed through your favorite package manager and the fusepy and requests libraries

In Windows:
Not supported.

Example to see some test files in the test folder.
Using the bitcoinfs.conf in the same folder:
./bincoinfs.py test/
Loading bitcoinfs.conf from the blockchain
./bitcoinfs.py test/ 663274c2e741484d2c2d2901cab0372ea978da7b608f7e9c3e41a2bc8e99f440
./bitcoinfs.py test/ 3fa7bea2b9d2ab16d7ecea074e9b2277272b9e707d42f4d52d69b9f5272025c6
