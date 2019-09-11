# Linux Server & Item Catalog Web App

## Important Details
Domain: https://www.avensky.com/  
Server address: 52.42.100.188  

Test user login facebook  
Email: fpvppdriwv_1566701238@tfbnw.net  
Password: Password90!  

## Description
* This project uses queries to create, read, update, and delete from a database.
* It implements login and user authentication.
* It uses a combination programs configured on a Linux server
* Final version available at https://wwww.avensky.com/

## Project Goals
This project will create a database in which users can create, read, update,
and delete from a catalog of
vegan restaurants. For simplicity it only supports one state at this time.

## Programs and Technologies used
* Ubuntu 16.04 LTS
* Python 3
* python 2
* PostgreSQL
* Flask
* Apache2
* Mod-wsgi
* certbot
* oauth2client
* requests
* httplib2
* postgresql
* python-psycopg2
* python-sqlalchemy

## Configurations made to server on server providers site
* Created a static ip
* Changed to custom ssh port
* Added port to allow https

## Security and server changes
* Updated all packages
* Enforced key authentication
* Set up Firewall to allow http, https, ssh, ntp
* Disabled Root Login
* Changed time zone
* Changed connection port
* Created postgreSQL database and user
* Configured apache to serve flask app using mod-wsgi
* Installed certbot to secure connetion/enable HTTPS

## Domain
* routed domain name to server

## Resources used to complete project  
https://www.youtube.com/watch?v=goToXTC96Co&t=183s  
https://www.youtube.com/watch?v=LUFn-QVcmB8  
https://www.youtube.com/watch?v=Gdys9qPjuKs  
https://certbot.eff.org/  
https://tecadmin.net/install-apache-mod-wsgi-on-ubuntu-16-04-xenial/  
https://www.digitalocean.com/community/tutorials/how-to-set-up-apache-virtual-hosts-on-ubuntu-14-04-lts
