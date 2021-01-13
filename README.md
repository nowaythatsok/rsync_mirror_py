# Rsync Mirror 

This is a small python script I use to make a MIRROR COPY of my hard disc every now and then on Windows. Since the tool uses RSYNC it has to be run using WSL2 (which is a blessing). 

Run the code with 
```sh
python3 rsync_mirror.py
```
and follow the instructions. It is very fool proof as long as you understand that this is a MIRROR tool. 

**Files in the destination that are not present in the source will be lost, potentially forever.**

## Setting up the default source and destination

At the very top of `rsync_mirror.py` you can modify 
```python
DEFAULT_SOURCE      = "/mnt/d"
DEFAULT_DESTINATION = "/mnt/f"
```
which is now set up for the test directories. 

In WSL2 the drives are mounted in `/mnt/` under their Windows drive letter. 
