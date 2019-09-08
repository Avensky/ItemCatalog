Linux server/ Item Catalog

This project uses queries to make create, read, update, and delete from a database.
And it also implements login and user authentication.

Project Goals
1) Create a database for vegan restaurants using our own server

Programs and Technologies used:
godaddy hostname
Linux-based virtual machine (Lightsail)
Ubuntu 16
Python 3
python 2
PostgreSQL
Flask
Apache2
Mod-wsgi
certbot

Test user login facebook
Email: fpvppdriwv_1566701238@tfbnw.net
Password: Password90!

Linux virtual machine serving flask app with mod wsgi
Server address: 52.42.100.188

ssh port 2200
secret key id_rsa:
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCydAwKwvJNSig4bTPa0Wsi8yYJaLPU6na/yXCJTEWbCDPv5XByQiHisC8HZdclYhYNyPfnA0zQNmBMkA79GfBw1Sq6oGV0PnIdmCKvUJcJqKWbt5u8f4aTT+D13vZbfIfm6bwqDI9YqHI8CVwUSTEPLvJo0huvwtghCMUX+KvQLh12+CRG052nGXjC7nnlC4IXkJWTRrAFk4apOaWLOzd3nvPImiEVkmJo9Kn/rEKdSExayi2TsrPJOMjDK5MX1uEUgY2dk84nrywodB8s1irMCt0OKGpwt97uwMaMOA19bHPIwfjTWoH92pI2rTG1VdPgLPLDgpoxZUW52KbQ1dxz uriel@DESKTOP-F4V9OGN

Set up Amazon Lightsail instance
Select Linux/Unix Ubuntu 16 LTS
Go to Networking tab and addn 
	custom   tcp   2200
	custom   tcp   5000
	custom   udp   123

Complete Step by Step process to setting up the server

Connect via ssh
Update Current packages
sudo apt update
sudo apt upgrade
	accept changes but also keep local versions currently installed
sudo apt autoremove

Set up Firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 2200/tcp
sudo ufw allow www
sudo ufw allow ntp
sudo ufw enable

create user
sudo adduser grader
pw: 32cats
sudo cp /etc/sudoers.d/90-cloud-init-users /etc/sudoers.d/grader
sudo nano /etc/sudoers.d/grader
	grader ALL=(ALL) NOPASSWD:ALL
sudo nano /etc/ssh/sshd_config
	Permit Root Login yes
	Password Authentication yes
sudo reboot

In local environment
	ssh-keygen
	c/users/uriel/.ssh/id_rsa: 

ssh to server
	ssh grader@52.42.100.188
	mkdir .ssh
	touch .ssh/authorized_keys
	nano .ssh/authorized_keys
		ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCydAwKwvJNSig4bTPa0Wsi8yYJaLPU6na/yXCJTEWbCDPv5XByQiHisC8HZdclYhYNyPfnA0zQNmBMkA79GfBw1Sq6oGV0PnIdmCKvUJcJqKWbt5u8f4aTT+D13vZbfIfm6bwqDI9YqHI8CVwUSTEPLvJo0huvwtghCMUX+KvQLh12+CRG052nGXjC7nnlC4IXkJWTRrAFk4apOaWLOzd3nvPImiEVkmJo9Kn/rEKdSExayi2TsrPJOMjDK5MX1uEUgY2dk84nrywodB8s1irMCt0OKGpwt97uwMaMOA19bHPIwfjTWoH92pI2rTG1VdPgLPLDgpoxZUW52KbQ1dxz uriel@DESKTOP-F4V9OGN 
	chmod 700 .ssh
	chmod 644 .ssh/authorized_keys

sudo nano /etc/ssh/sshd_config
	port 2200
	PermitRootLogin no
	Password Authentication no
sudo service ssh restart
sudo reboot
ssh grader@52.42.100.188 -p 2200
Check status to remove old ports
	sudo ufw status
	sudo ufw delete #
	
sudo timedatectl set-timezone UTC
Install dependencies and virtual environment

	sudo apt-get install python libexpat1 
	sudo apt-get install apache2 apache2-utils ssl-cert
	sudo apt-get install libapache2-mod-wsgi
	sudo systemctl restart apache2
	sudo git clone https://github.com/Avensky/ItemCatalog.git /var/www/html/ItemCatalog
		removed old files & renamed main file to __init__.py
	sudo apt-get install python3-venv
	sudo python3 -m venv venv
	source /var/www/html/venv/bin/activate
	sudo apt-get install python-pip
	sudo python -m pip install --upgrade pip
	sudo python2 -m pip install oauth2client
	sudo python2 -m pip install requests
	sudo python2 -m pip install httplib2	
	sudo apt-get -qqy install postgresql python-psycopg2

Configure Apache, mod-wsgi
	sudo nano /etc/apache2/sites-available/000-default.conf
		<VirtualHost *:80>
			ServerName avensky.com
			ServerAdmin urielzacarias@gmail.com
			WSGIScriptAlias / /var/www/html/ItemCatalog/myapp.wsgi
			<Directory /var/www/html/ItemCatalog>
				Order allow,deny
				Allow from all
			</Directory>
			
			Alias /static /var/www/html/ItemCatalog/static
			<Directory /var/www/html/ItemCatalog/static/>
				Order allow,deny
				Allow from all
			</Directory>
			
			ErrorLog ${APACHE_LOG_DIR}/error.log
			LogLevel warn
			CustomLog ${APACHE_LOG_DIR}/access.log combined
		</VirtualHost>
	sudo a2ensite ItemCatalog

	sudo nano /var/www/html/ItemCatalog/myapp.wsgi
		#!/usr/bin/python
		import sys
		import logging
		sys.path.append('/var/www/html/ItemCatalog')
		from __init__ import app as application
		application.secret_key = 'super_secret_key'
	sudo service apache2 restart

Make sure that your .git directory is not publicly accessible via a browser!

Install and configure postgreSQL database and user
	sudo apt-get install postgresql 
	sudo apt-get install python-sqlalchemy
	Do not allow remote connections
		sudo nano /etc/postgresql/9.5/main/pg_hba.conf
	sudo su postgres
	createuser --interactive --pwprompt
		Enter name of role to add: catalog
		Enter password for new role:
		Enter it again:
		Shall the new role be a superuser? (y/n) n
		Shall the new role be allowed to create databases? (y/n) y
		Shall the new role be allowed to create more new roles? (y/n) n
		createdb -O catalog catalog
	exit
Edit database_setup.py, __init__.py and change
	sudo nano /var/www/html/ItemCatalog/__init__.py
		edit CLIENT_ID to look like this

		with app.open_resource('client_secrets.json') as f:
			CLIENT_ID = json.load(f)['web']['client_id']

		change end to this
		if __name__ == '__main__':
				app.secret_key = 'super_secret_key'
				app.config['SESSION_TYPE'] = 'filesystem'
				app.debug = True
				app.run()
	change db engine
		#engine = create_engine('sqlite:///db.db')
		engine = create_engine('postgresql://catalog:password@localhost/catalog')		
	sudo nano /var/www/html/ItemCatalog/database_setup.py
	sudo python database_setup.py
sudo service apache2 restart

sudo nano /etc/hosts
52.42.100.188 avensky.com

Configure and install software to enable HTTPS 
	audo apt-get update
	sudo apt-get install software-properties-common
	sudo add-apt-repository universe
	sudo add-apt-repository ppa:certbot/certbot
	sudo apt-get update

	sudo apt-get install certbot python-certbot-apache
	sudo certbot --apache
