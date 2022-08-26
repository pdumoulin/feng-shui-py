feng-shui-py
=====
Automatically links home directory files to conf directory for cloud backup and generates package lists for popular managers.

```
usage: cli.py [-h] [--conf CONF] [--env ENV] [--box BOX] {link,init,store,package} ...

positional arguments:
  {link,init,store,package,clean}
    link                symlink files from conf storage dir to home dir
    init                initialize new conf storage dir
    store               move file from home dir to conf storage dir
    package             manage system installed packages
    clean               remove broken symlinks in home dir

optional arguments:
  -h, --help            show this help message and exit
  --conf CONF           override default conf dir: "default-value-here"
  --env ENV             override default env dir: "default-value-here"
  --box BOX             override default box dir: "default-value-here"
```

### Configuration

Commands are always executed in the context of a single box being configured.

| name | cli flag | envvar | default | description |
| ------------- | ------------- | ------------- | ------------- | ------------- |
| env  | `--env`  | `$FS_ENV`  | user prompt | category of box (ex. home, work)           |
| box  | `--box`  | `$FS_BOX`  | user prompt | specific name of box (ex. laptop, desktop) |
| conf | `--conf` | `$FS_CONF` | `./conf/`  | directory to store configurations   |

Data is read in the following order of precedence:
* cli flag
* envvar
* default

:bulb: To see defaults for your current context, run `$ python cli.py --help` and look in the `optional arguments` section.

:bulb: By default conf directory used is `./conf/` inside of **this project** which is automatically ignored by git.

:warning: Be sure to set the conf directory to be another git repo or directory that is synced with a cloud service to backup your data.

:+1: Add environment variables in your `~/.bashrc` for each managed box to automatically set the context.

### Initialize
Create a new configuration directory setup for a specific box, and global conf directory if needed. Optionally clone an existing box conf directory.

```
usage: cli.py init [-h] [--clone CLONE CLONE]

optional arguments:
  -h, --help           show this help message and exit
  --clone CLONE CLONE  two values, "env box" to clone files from
```


### Store
Move a single file or directory to the conf directory and symlink it to your home directory.

```
usage: cli.py store [-h] [-f] [-g] target

positional arguments:
  target      file or dir to move and symlink, must be in home dir

optional arguments:
  -h, --help  show this help message and exit
  -f          do not prompt on overwrite
  -g          store in global conf dir
```

### Link
Create symlinks in home directory based on files and directories in your conf directory.

```
usage: cli.py link [-h] [-g] [-f] [-b] [-s]

optional arguments:
  -h, --help  show this help message and exit
  -g          apply global settings
  -f          do not prompt on remove/move step
  -b          create backup if file already exists
  -s          create links for scripts
```

### Package
Manage packages installed. Metadata files will be stored in your conf directory.

```
usage: cli.py package [-h] {brew,apt-clone,pip,npm} {backup,restore,list}

positional arguments:
  {brew,apt-clone,pip}  package management category
  {backup,restore,list}
                        operation to perform

optional arguments:
  -h, --help            show this help message and exit
```

### Clean

Remove broken symlinks in home dir.

```
usage: cli.py clean [-h] [-f]

optional arguments:
  -h, --help  show this help message and exit
  -f          do not prompt on remove
```
