# Farmware Tools
Tools for use by [Farmware](https://software.farm.bot/docs/farmware-dev).

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

## Local installation
```
git clone https://github.com/FarmBot-Labs/farmware-tools
cd farmware-tools/
pip install .
```
