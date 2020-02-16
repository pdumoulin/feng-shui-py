feng-shui-py
=====
Python re-implementation of home directory configuration project. Box specific configurations not included.

```bash
usage: linker.py [-h] [--conf CONF] [-g] [-f] [-b] [-s] environment box

positional arguments:
  environment  category of box
  box          box specific settings

optional arguments:
  -h, --help   show this help message and exit
  --conf CONF  override default conf dir @ "/home/paul/feng-shui-py/conf"
  -g           apply global settings
  -f           do not prompt on remove/move step
  -b           create backup if file already exists
  -s           create links for scripts
```
