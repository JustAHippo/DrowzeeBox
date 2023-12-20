# DrowzeeBox
Self-hosted file sharing using the Discord CDN
## Setup
Make a copy of config.example.json and name it config.json.

Next, enter a key that you want to use for encryption. You can generate one like this:
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode("utf8"))
```
For caching and databasing, you will need a MongoDB and Redis DB

Last, enter your webhook into the field, if there is a slash at the end, remove it.

Now, you can run with

```
uvicorn main:app --host 0.0.0.0 --port 80
```

PLEASE NOTE: If you experience issues with memory usage, add --reload. Be aware that this can significantly increase CPU usage under some circumstances, as it will check the filesystem fairly often.


## NOTICE
This tool is very likely against the Discord terms of service. I am not responsible for any account bans or restrictions that occur due to the use of DrowzeeBox. Out of personal caution, I would not recommend either storing important files, using this tool on your main Discord account, or publicly sharing links to downloads from DrowzeeBox(downloads are slightly resource intensive & uploads are not restricted)

Intended for personal use rather than public.
