# bitcoinfs
FUSE interface for blockchain file storage
Uses fusepy library,requires a local or remote trusted bitcoind daemon with bitcoin-cli read access

Example to see some test files in the test folder.
./bitcoinfs.py test/ 663274c2e741484d2c2d2901cab0372ea978da7b608f7e9c3e41a2bc8e99f440
./bitcoinfs.py test/ 845615a2c3f676072924c34fec6d41b5d943cea901c107bb6e4695cf44343b6b
