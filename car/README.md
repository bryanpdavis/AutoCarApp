Install Node
curl -sL https://deb.nodesource.com/setup_7.x | sudo -E bash -
sudo apt install nodejs

See if it's installed
node -v

Make file node.js server start at bootup by editing /etc/rc.local
https://createweb.be/wp-content/uploads/2017/05/raspisensor_boot.png
Using this line:
su pi -c 'sudo node /home/pi/AutoCarApp/car/index.js < /dev/null &'