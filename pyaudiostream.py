import subprocess
import re

# executeute a given commands with given arguments and return terminal response and error
def execute(command, *args):
    proc = subprocess.Popen([command, *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    response, err = proc.communicate()
    # Returns a clean version of response and err
    return response.decode("utf-8").strip(), err.decode("utf-8").strip()


def getStreamsOnly():
    cardsPath = "/proc/asound/cards"
    cardRoot = "/proc/asound/card"

    # Get the cards
    r, err = execute("cat", cardsPath)

    # If an error is detected
    if err != "": 
        print("ERROR: {}\nExit!".format(err))
        exit(-1)

    # Get active cards recognized by ALSA
    chunks = r.split("\n")
    cards = [card for i, card in enumerate(chunks) if i%2==0 and card != '']
    
    # Extract cards indexes from cards names
    cardIndexes = [i.strip()[0] for i in cards]

    active_streams = []

    # Seearch for active streams for each card and fill
    # the active_streams list
    for i in cardIndexes:
        # Get card streams
        r, err = execute("ls", "{}".format(cardRoot+i))
        # Skip the reading in case of error
        if err != "":
            continue

        # Get all the streams (using regex)
        streamFolders = [stream for stream in r.split("\n") if re.match("^pcm\d+p", stream)]
        # Skip the reading in case of no results found
        if len(streamFolders) == 0:
            continue
        
        # Search substreams
        for streamFold in streamFolders:
            r, err = execute("ls", "{}/{}".format(cardRoot+i, streamFold))
            # Get all the substreams (using regex)
            substreamFolders = [sub for sub in r.split("\n") if re.match("^sub\d", sub)]
            # Skip the reading in case of no results found
            if len(substreamFolders) == 0:
                continue

            # Read each substream
            for subFold in substreamFolders:
                # Get streams parameters such as sampling rate, format, channels, etc..
                r, err = execute("cat", "{}/{}/{}/hw_params".format(cardRoot+i, streamFold, subFold))
                # Skip the reading in case of error
                if err != "":
                    continue

                # Is substream is not closed
                if r != "closed":
                    # Get the cardID
                    cardID, err = execute("cat", "{}/id".format(cardRoot+i))
                    # Skip the reading in case of error
                    if err != "":
                        continue

                    # Expected location of ALSA audio stream
                    # Format: pcmC{number_of_card}D{number_of_stream}p
                    audioStreamPath = "/dev/snd/pcmC{}D{}p".format(i, streamFold[-2])
   
                    stream_info = {"Card":cardID, "CardPath":cardRoot+i, "Stream":streamFold, "Substream":subFold, "AudioStreamPath":audioStreamPath, "Params":r}
                    #stream_info = [cardID, streamFold, subFold, audioStreamPath, r]
                    active_streams.append(stream_info)

    # If no streams have been found, just return an empty list
    if len(active_streams) == 0:
        return []
    
    # Return the active streams
    return active_streams

    
def addProcessesNames(active_streams):
    # This script searches for symlinks into /proc/
    # that point into /dev/snd/ and are pcm streams
    # Remember that # in bash means "remove from $var the shortest part of a pattern"
    #E.g: var = /dev/snd/pcmC1D0p -> ${var#/dev/snd/pcm} == C1D0p -> C1D0p != $var
    script = """
            #!/bin/bash
            # For each element in /proc that starts with a number
            # (they are symbolic links)
            for i in /proc/[0-9]*/fd/*
            do
                # Read the destination of the symlink
                var="$(readlink $i)"
                # Subtract the string "/dev/snd/pcm" from
                # the destination: if the string changes from the original
                # it means that the symlink points to /dev/snd/pcmXX
                # (it was actually subtracted),
                # which is exactly what we are searching for
                if [ "$var" != "${var#/dev/snd/pcm}" ]
                then
                    # echo the symlink and the destination into stdout
                    echo $i:$var
                fi
            done
            """
    # Call a script that search for the processes that
    # are using ALSA
    r, err = execute("bash", "-c", script)

    if r == "":
        return []
    
    processesInfo = r.split("\n")
    
    # For each process
    for i, proc in enumerate(processesInfo):
        # Get infos about the process
        procPath, audioPath = proc.split(":")
        PID = procPath.split("/")[2]
        # Get the process name
        name, err = execute("ps", "-p", PID, "-o", "comm=")
        if err != "":
            print("ERROR: can't obtain process name for PID", PID)
            return []

        # Link the process name to the stream by shared AudioStreamPath
        for j, v in enumerate(active_streams):
            if audioPath == active_streams[j]["AudioStreamPath"]:
                active_streams[j]["ProcessName"] = name
                active_streams[j]["PID"] = PID


    return active_streams

def prettifyParams(params):
    p = params.split("\n")
    
    # Create the new bits field (search for 8, 16, 24, 32 or 64 and
    # crop it from the format string)
    fnd = [e for e in ["8", "16", "24", "32", "64"] if e in p[1]]
    pos = p[1].find(fnd[0])
    bits = p[1][pos : pos + len(fnd[0])]

    # Insert the new field into the original params
    p.insert(1, "bit_depth: {}".format(bits))
    
    # Edit the rate field and add "Hz"
    rate_chunks = p[5].split(" ")
    rate_chunks[1] = "{} Hz".format(rate_chunks[1])
    # Insert the rate into first posisition (was at 5)
    p.insert(1, " ".join(rate_chunks))
    # Elements from pos 1 shifted by one, so old rate was at 6. Deletes it.
    del p[6]

    
    # Add a tab for each field
    p = ["   "+c for c in p]
    
    # Join the result and return
    return "\n".join(p)


def GetActiveStreams(includeProcName = False):
    active_streams = getStreamsOnly()

    # Search for processes name only if the flag is true and
    # at least one stream has been found
    if includeProcName and len(active_streams) > 0:
        active_streams = addProcessesNames(active_streams)

    return active_streams


def PrettyPrint(active_streams):
    print("Found {} active".format(len(active_streams)), ["stream" if len(active_streams) == 1 else "streams"][0])
    
    for i, stream in enumerate(active_streams):
        params = prettifyParams(stream["Params"])
        print("{}:".format(i))
        print("   device_name: {}\n   device_path: {}\n   process_name: {} (PID {})\n{}\n   stream_name: {}\n   substream_name: {}\n   audio_path: {}\n".format(
              stream["Card"], stream["CardPath"], stream["ProcessName"], stream["PID"], params, stream["Stream"], stream["Substream"], stream["AudioStreamPath"]))

print("--- Starting audiostream version 1.0 ---")
print("Searching...\n")

active_streams = GetActiveStreams(True)

if len(active_streams) == 0:
    print("No streams have been found!")
    exit()
    
PrettyPrint(active_streams)
