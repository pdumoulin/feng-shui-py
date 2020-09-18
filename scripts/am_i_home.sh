HOME=$(dig +short discoghost.duckdns.org)
CURRENT=$(curl -s ifconfig.co)
echo "home    => $HOME"
echo "current => $CURRENT"
if [ "$HOME" == "$CURRENT" ]; then
    echo "yes"
    exit 0
fi
echo "no"
exit 1 
