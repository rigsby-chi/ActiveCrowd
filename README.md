# Welcome to ActiveCrowd.
**Active Crowd** is an automated active learning framework that enable users to perform **low cost and efficient supervised learning** for classification 
under environment that labels are not provided along with samples. It can select the most desirable samples to be labeled and thus dramatically the cost of 
labeling and learning. Moreover, the **ActiveCrowd framework** provides the ability of submitting samples to **Amazon Mechanical Turk** so you can obtain 
scalable and on-demand workforce to perform labeling labels instead of labeling samples by yourself. Comprehensive monitoring and performance evaluation tools 
are also provided to adjust the learning direction, assess the learning efficiency and improve classification accuracy.  

To run the framework, switch the current directory to the framework location and execute run.py:  
```
$ cd <path_to_framework>/ActiveCrowd
$ python run.py
```  
Then you can access the framework via any browser as follow:   
            
![Home Page](http://i.imgur.com/bZATTVB.png)  
_*This framework is design for Linux. No Windows version is available for now._
  
***
## 1. Installation and Setup
### 1. 1 Necessary software and packages
To use the ActiveCrowd framework, first you need Python, PostgreSQL and some libraries installed:  
* Python 2.7  
* PostgreSQL
* Java Runtime Environment (JRE)
* NumPy
* scikit-learn
* Psycopg2 
* Flask

If you are using Ubuntu, you can install the above packages with the following commands:
```
sudo add-apt-repository ppa:fkrull/deadsnakes
sudo apt-get update
sudo apt-get install python2.7
sudo apt-get install postgresql postgresql-contrib
sudo apt-get install default-jre
sudo apt-get install python-numpy
sudo apt-get install python-sklearn
sudo apt-get install libpq-dev
sudo apt-get install python-pip
sudo pip install Flask
sudo pip install psycopg2
```  

You also need to set the "JAVA_HOME" environment variable. Execute the following command to find out the path to java.
```
sudo update-alternatives --config java
```  
Then execute the command:
```
sudo gedit /etc/environment
```  
Add a new row and save the file:
```
JAVA_HOME="Path_To_Java"
```
Finally, reload the file:
```
source /etc/environment
```

### 1. 2 PostgreSQL Configuration
It is recommended that an independent database and database user are created for the framework. To do so, you may execute the following commands:
```
$ sudo su - postgres
$ createdb activecrowd
$ psql -s activecrowd
# create user <user_name> password '<user_password>';
# GRANT ALL PRIVILEGES ON DATABASE activecrowd TO <user_name>;
```

Also, you need to change the authentication method from peer to md5 by executing the following command to open `pg_hba.conf`:
```
sudo gedit /etc/postgresql/9.3/main/pg_hba.conf
```
Find the following line:
```
local   all             all                                     peer
```
Replace peer to md5:
```
local   all             all                                     md5
```
Save the file and execute `sudo service postgresql restart` to restart PostgreSQL

### 1. 3 Framework Setup
Switch terminal's current directory to the unzipped framework folder and execute run.py:  
```
$ cd <path_to_framework>/ActiveCrowd
$ python run.py
```  
Then you can access the framework on any browser. The first launch of the framework require a simple setup operation. First you need to provide database name, 
database user and database user password (as created in 1. 2):   
     
![Framework first launch setup](http://i.imgur.com/6XtDAWJ.png)
