# bitcoinfs


FUSE interface for blockchain file storage


mount a local folder with files from bitcoinSV blockchain 



Requires python3 with the fusepy and requests libraries.
bitcoin-cli is required to use the file upload scripts

# Installation

* Using pip and local python enviroment. Recomended
```
pip install virtualenv
```
```
virtualenv -p python3 envname
```
```
source envname/bin/activate
```
```
pip3 install fusepy
```
```
pip3 install requests
```

* In Ubuntu Linux 18.04:

```
apt-get install python3-fusepy python3-requests
```

* In OSX:

Not tested due to no available machine, but it should work with MacFUSE installed through your favorite package manager and the fusepy and requests libraries

* In Windows:

Not supported.

#Usage
To mount from BitcoinsSV trasnsaccion ID in mnt existing folder

```
./bitcoinfs.py mnt/ txid
```

# Use Cases 

* 1 Loading bitcoinfs.conf from the blockchain

```
./bitcoinfs.py test/ 663274c2e741484d2c2d2901cab0372ea978da7b608f7e9c3e41a2bc8e99f440
```

* 2 Mounting Riemann Paper and four strand DNA olygo assembler sequence, Pubmed ID [30285239](https://www.ncbi.nlm.nih.gov/pubmed/30285239)

```
./bitcoinfs.py test/ 3fa7bea2b9d2ab16d7ecea074e9b2277272b9e707d42f4d52d69b9f5272025c6
```
# ARTEFACTS

* Mount Human Transcriptome

* Mount Human Proteome [UP000005640](https://www.uniprot.org/proteomes/UP000005640)
