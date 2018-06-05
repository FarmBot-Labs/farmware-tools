# Farmware Tools
Tools for use by [Farmware](https://developer.farm.bot/docs/farmware). __Starting with FarmBot OS v6.4.2, this package is installed automatically and available for Farmware to import.__ See the sections below for other installation configurations.

## Example
```Python
from farmware_tools import device
device.log('hello')
```
If the above code is run within a Farmware,
[FarmBot OS](https://github.com/FarmBot/farmbot_os)
will send a `hello` log to the
[FarmBot Web App](https://my.farm.bot/).

If the above code is run elsewhere,
the output will be the command that would have been sent to FarmBot OS:
```
{'kind': 'send_message', 'args': {'message': 'hello', 'message_type': 'info'}}
```

## Documentation
In addition to the [Farmware development documentation](https://developer.farm.bot/docs/farmware),
a list of available functions is available via the Python console:
```Python
from farmware_tools import app, device
help(app)
help(device)
```

## Local installation (for local Farmware development)
```
pip install farmware-tools
```
_user-level install_: `pip install --user farmware-tools`

_upgrade_: `pip install --user --upgrade farmware-tools`

_install a specific version_: `pip install --user farmware-tools==1.0.0`

## Specifying a version in a Farmware manifest
```
"farmware_tools_version": "v1.0.0"
```
By including this line in a Farmware
[manifest](https://developer.farm.bot/docs/farmware#section-farmware-manifest),
FarmBot OS will automatically install the specified version
and make it available to import from within the Farmware.
