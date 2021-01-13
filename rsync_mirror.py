from __future__ import print_function
import subprocess, shlex, sys
from termcolor import colored, cprint
from time import sleep, time, strftime
import os
from os.path import exists, join, isdir

try:
    input = raw_input
except NameError:
    pass

DEFAULT_SOURCE      = "/mnt/d"
DEFAULT_DESTINATION = "/mnt/f"
DEFAULT_SOURCE      = "test_dir1"
DEFAULT_DESTINATION = "test_dir2"
SYNC_COUNTDOWN      = 10
EXCLUDED_SYS_FILES  = ["\"System Volume Information\"", "\"Recovery\"", "\"$RECYCLE.BIN\""]

"""
-a, --archive               archive mode; equals -rlptgoD (no -H,-A,-X)
    -r, --recursive             recurse into directories
    -l, --links                 copy symlinks as symlinks
    -p, --perms                 preserve permissions
    -t, --times                 preserve modification times
    -g, --group                 preserve group
    -o, --owner                 preserve owner (super-user only)
    -D                          same as --devices --specials
        --devices               preserve device files (super-user only)
        --specials              preserve special files
-u, --update            skip files that are newer on the receiver
-b, --backup                make backups (see --suffix & --backup-dir)
    --backup-dir=DIR        make backups into hierarchy based in DIR
    --suffix=SUFFIX         set backup suffix (default ~ w/o --backup-dir)
-i, --itemize-changes       output a change-summary for all updates
-c, --checksum              skip based on checksum, not mod-time & size
-v, --verbose               increase verbosity
-q, --quiet                 suppress non-error messages
-h, --human-readable        output numbers in a human-readable format
-n, --dry-run               perform a trial run with no changes made
--delete                delete extraneous files from dest dirs
-P                          same as --partial --progress
    --partial               keep partially transferred files
    --progress              show progress during transfer
--stats                 give some file-transfer stats

If only permissions change then rsync is smart enough to not transfer the fil, but just chmod. Permissions mean nothing on NTFS anyways. 
"""
def cmdWaitRsync(command, printRealTime=False, totalTransferSize_bytes=1, start=0):
    process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    output = ""
    error  = None
    if not printRealTime:
        output, error = process.communicate()

        try:
            output = output.decode("utf-8")
        except (UnicodeDecodeError, AttributeError):
            pass
        
    else:
        sizeDone = 0.0
        for line in iter(process.stdout.readline, b''):

            try:
                line = line.decode("utf-8")
            except  (UnicodeDecodeError, AttributeError):
                pass

            output += line
            print(line.replace('\n', ''))
            split_line = line.split()
            if totalTransferSize_bytes>1 and len(split_line)>5 and split_line[-5]=="100%":
                try:
                    fileSize  = hrSize2bytes(split_line[-6])
                    sizeDone += fileSize
                    ratio     = sizeDone/totalTransferSize_bytes
                    t_str   = ""
                    if ratio>0.01:
                        t_str = " Elapsed: {} TREM: {}".format(dt2hrDt( (time()-start)), dt2hrDt( (time()-start)*(1/ratio-1) ))
                    print(colored("{:.1%}{}".format(ratio, t_str), "yellow"))
                except:
                    pass

        error = process.stderr.read()

    try:
        error = error.decode("utf-8")
    except  (UnicodeDecodeError, AttributeError):
        pass

    if not error is None and len(error)>0:
        print(colored(" ".join([command, ":", error]), "red"))

    return output


def disclaimer():
    print(colored("""
    WARNING: This code SYNCs two directories. 
    This means that files not present at the source will be REMOVED from the destination. 
    This can lead to IRRECOVERABLE DATALOSS if you give the wrong destination. 
    Only new and files with mismatching size or timestamps are copied. 
    Files with identical name, size and timestamps are considered the same. 
    Checksums are not computed. 
    If a file at the source is older then at the destination the destination file will STILL BE OVERWRITTEN.
    """, "red"))
    proceed()

def proceed():
    proceed_ans = input("Would you like to proceed? (Y/n) ")
    while not proceed_ans in ["Y", "n"]:
        proceed_ans = input("Make sure you answer either Y or n: ")
    if proceed_ans != "Y":
        print(colored("Aborting!", "green"))
        sys.exit(1)

def askSDInput(kind, default):
    if exists("/mnt"):
        mounted = [d for d in os.listdir("/mnt") if isdir(join("/mnt",d))]
        print("Your mounted volumes in \"/mnt\": {}".format(" ".join(mounted)))
    path = " ;"*10
    while not exists(path):
        path = input("Please provide the path to the {} dir: ".format(kind))
        if not exists(path):
            print(colored("This place doe not exist :(", "red"))
        else:
            print(colored("Perfect!", "green"))
    
    return path

def selectSDItem(kind, default):
    if not exists(default):
        print(colored("Your default {} does not exist. Please specify a new one!".format(kind), "yellow"))
        return askSDInput(kind, default)

    else:
        print("Your default source \"{}\" is accesible".format(default))
        ans = input("Would you like to specify a different {}? (Y or n) ".format(kind))
        while not ans in ["Y", "n"]:
            ans = input("Make sure you answer either Y or n: ")
        if ans == 'n':
            return default
        else:
            return askSDInput(kind, default)

def selectSourceAndDest():
    print(colored("Select your source and destination!", "yellow"))

    source      = selectSDItem("source", DEFAULT_SOURCE)
    destination = selectSDItem("destination", DEFAULT_DESTINATION)

    if destination.startswith(source) or source.startswith(destination):
        print(colored("Source and destination cannot be on the same path!", "red"))
        sys.exit(1)

    if destination.startswith("/mnt/c"):
        print(colored("For your own safety, I wont let you write to C", "red"))
        sys.exit(1)

    
    print(source, "-->", destination)
    return source, destination

def dryRun(source, destination, wait_for_res=2, excludeWinSysFiles=True, doDelete=True):
    print(colored("Performing dry run!", "yellow"))
    start = time()

    exclusions = ""
    if excludeWinSysFiles:
        exclusions = " --exclude=".join([""]+EXCLUDED_SYS_FILES)
    delete = ""
    if doDelete:
        delete = " --delete"
    # command = "rsync -aivhn --no-p {}/ {}/ --stats{}{}".format(source, destination, exclusions, delete)
    command = "rsync -aivhn {}/ {}/ --stats{}{}".format(source, destination, exclusions, delete)
    print(colored(command, "yellow"))

    dryRun_results = cmdWaitRsync(command)

    if time()-start<2:
        sleep(wait_for_res-(time()-start))
    if dryRun_results.count('\n')<1000:
        print(dryRun_results)
    else:
        print('Too many lines to output here. Summary:')
        print("="*15)
        print(dryRun_results.split("\n\n")[-2])
        print("="*15)
    with open("dryRun.txt", "w") as f:
        f.write(dryRun_results)
    print(colored("Dry run results were written to dryRun.txt !", "yellow"))

    totalTransferSize_line = [ x for x in dryRun_results.split("\n")[-20:] if x.startswith("Total transferred file size:")][0]
    totalTransferSize_str = totalTransferSize_line.split(" ")[4]
    totalTransferSize_bytes = hrSize2bytes(totalTransferSize_str)

    print("="*15)

    ###
    n = dryRun_results.count(">f+++++++++")
    c = "red"
    if (n>0):
        c = "yellow"
    print(colored("New files: {}".format(n), c))

    ###
    n = dryRun_results.count(">f") - dryRun_results.count(">f+++++++++")
    c = "green"
    if (n>0):
        c = "red"
    print(colored("Modified files to be overwritten all: {}".format(n), c))

    ###
    n = dryRun_results.count(">f.s")
    c = "green"
    if (n>0):
        c = "red"
    print(colored("Modified files to be overwritten due to size difference: {}".format(n), c))

    ###
    n = dryRun_results.count("*deleting")
    c = "green"
    if (n>0):
        c = "red"
    print(colored("Files to be deleted: {}".format(n), c))
    
    ###
    print(colored("Delta = {}".format(totalTransferSize_str), "yellow"))


    print("="*15)
    
    return totalTransferSize_bytes

def sync(source, destination, totalTransferSize_bytes=1, excludeWinSysFiles=True, doDelete=True):

    exclusions = ""
    if excludeWinSysFiles:
        exclusions = " --exclude=".join([""]+EXCLUDED_SYS_FILES)
    delete = ""
    if doDelete:
        delete = " --delete"
    # command = "rsync -ahP --no-p {}/ {}/ --outbuf=L{}{}".format(source, destination, exclusions, delete)
    command = "rsync -ahP {}/ {}/ --outbuf=L{}{}".format(source, destination, exclusions, delete)
    print(colored(command, "red"))

    for i in range(SYNC_COUNTDOWN, 0, -1):
        print(colored("Syncing will start in {} seconds. Ctrl+C to cancel".format(i), "red"))
        sleep(1)

    print(colored("Syncing!", "yellow"))
    
    cmdWaitRsync(   command, 
                    printRealTime=True, 
                    totalTransferSize_bytes=totalTransferSize_bytes, 
                    start=time())

def dt2hrDt(dt):
    seconds = int(dt)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return "{}d {}:{}:{}".format(days, hours, minutes, seconds)
    elif hours > 0:
        return "{}:{}:{}".format(hours, minutes, seconds)
    elif minutes > 0:
        return "{}m {}s".format(minutes, seconds)
    else:
        return "{}s".format(seconds)

def hrSize2bytes(hrSize):
    sizeInBytes = 0
    if not hrSize[-1].isdigit():
        sizeInBytes = float(hrSize[:-1])
        if hrSize[-1].lower() == "k":
            sizeInBytes *= 10**3
        elif hrSize[-1].lower() == "m":
            sizeInBytes *= 10**6
        elif hrSize[-1].lower() == "g":
            sizeInBytes *= 10**9
        elif hrSize[-1].lower() == "t":
            sizeInBytes *= 10**12
        else:
            raise NotImplementedError("hrSize[-1]: {}".format(hrSize[-1]))
    else:
        sizeInBytes = float(hrSize)
    return sizeInBytes

if __name__ == "__main__":

    start = time()

    disclaimer()
   
    source, destination = selectSourceAndDest()

    totalTransferSize_bytes = dryRun(source, destination)
   
    proceed()
    
    sync(source, destination, totalTransferSize_bytes)


    hrTime = dt2hrDt( time()-start )
    print(colored("The script finished succesfully in {} !".format(hrTime), "green"))
    
