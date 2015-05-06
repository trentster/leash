ZONEIP=`ifconfig | grep inet | grep -v '127.0.0.1' | grep -v '\:\:1/128' | awk '{print $2}' | head -n 1`

cat <<EOL
Zone prep complete!
***************************************************
* To begin install navigate to:                   *
*                                                 *
* Then in your browser navigate to:               *
*   http://$ZONEIP:5000                       *
*                                                 *
***************************************************
EOL
