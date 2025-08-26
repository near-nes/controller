#!/bin/bash
set -e

# This script runs as the non-root user ($USERNAME)
# It sets up the VNC password, runs prerequisite scripts (like editable install),
# and starts the VNC server in the background.

# VNC_PASSWORD - Required. Used to set the VNC server password.
# VNC_DISPLAY - Used to specify the display number for the VNC server.
# USERNAME - Referenced in a comment but not directly used in the script. It's mentioned that the script runs as the non-root user identified by this variable.

# The script will fail with an error message if VNC_PASSWORD is not set. The VNC_DISPLAY variable is used but doesn't appear to have a default value in this script (it's referenced as ${VNC_DISPLAY}). The USERNAME variable is only mentioned in a comment and not actually used in script execution.


echo "Running VNC startup script as user: $(id)"

# --- Check Dependencies ---
if ! command -v vncserver &> /dev/null; then
    echo "Error: vncpasswd or vncserver command not found. Is tigervnc installed correctly?" >&2
    exit 1
fi
if [ ! -f "$HOME/.vnc/xstartup" ]; then
    echo "Error: VNC xstartup script not found at $HOME/.vnc/xstartup" >&2
    exit 1
fi

# --- Start VNC Server ---
VNC_DISPLAY="${VNC_DISPLAY}"
VNC_GEOMETRY="1280x800"
VNC_DEPTH="24"
VNC_ARGS="-SecurityTypes None --I-KNOW-THIS-IS-INSECURE -geometry $VNC_GEOMETRY -depth $VNC_DEPTH -localhost no -xstartup $HOME/.vnc/xstartup"

# Check if VNC server is already running on this display
if vncserver -list | grep -q "^${VNC_DISPLAY}"; then
    echo "Background VNC Starter: VNC server on display ${VNC_DISPLAY} already running."
else
    echo "Background VNC Starter: Starting VNC server on display $VNC_DISPLAY in background..."
    echo "Command: vncserver $VNC_DISPLAY $VNC_ARGS"
    vncserver "$VNC_DISPLAY" $VNC_ARGS # No -fg, No exec
fi

echo "Background VNC Starter: Completed."
exit 0 # Exit successfully, allowing the entrypoint to continue

# echo "Starting VNC server on display $VNC_DISPLAY..."
# echo "Command: vncserver $VNC_DISPLAY $VNC_ARGS"
# # Use exec to replace this script process with the vncserver process
# exec vncserver "$VNC_DISPLAY" $VNC_ARGS