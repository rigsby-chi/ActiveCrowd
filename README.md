# Welcome to ActiveCrowd.
**ActiveCrowd** is an automated active learning framework that enables users to perform **low cost and efficient supervised learning** for classification under environment that labels are not provided along with samples. It can select the most desirable samples to be labeled and thus dramatically the cost of labeling and learning. Moreover, the **ActiveCrowd framework** provides the ability of submitting samples to **Amazon Mechanical Turk** so you can obtain scalable and on-demand workforce to perform labeling tasks instead of labeling samples by yourself. Comprehensive monitoring and performance evaluation tools are also provided for you to adjust the learning direction, assess the learning efficiency and improve classification accuracy.  

To run the framework, switch the current directory to the framework location and execute run.py:  
```
$ cd <path_to_framework>/ActiveCrowd
$ python run.py
```  
Then you can access the framework via any browser like the following:   
            
![Home Page](http://i.imgur.com/bZATTVB.png)  
_*This framework is designed for Linux. No Windows version is available for now._
  
***
## 1. Installation and Setup
### 1. 1 Necessary software and packages
To use the ActiveCrowd framework, you need Python, PostgreSQL and some libraries installed:  
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
sudo apt-get install build-essential python-dev python-pip \
                     python-setuptools python-numpy python-scipy \
                     libpq-dev libatlas-dev libatlas3gf-base \
                     postgresql postgresql-contrib \
                     default-jre
sudo update-alternatives --set libblas.so.3 \
    /usr/lib/atlas-base/atlas/libblas.so.3
sudo update-alternatives --set liblapack.so.3 \
    /usr/lib/atlas-base/atlas/liblapack.so.3
sudo pip install scikit-learn Flask psycopg2
```  

You also need to set the "JAVA_HOME" environment variable. Execute the following command to find out the path to java.
```
sudo update-alternatives --config java
```  
If it give you path `/usr/lib/jvm/java-7-openjdk-amd64/jre/bin/java`, then the path you need is `/usr/lib/jvm/java-7-openjdk-amd64`  

Open `/etc/environment` with read and write privilege, and add the following row:
```
JAVA_HOME="Path_To_Java"
```
Finally, save the file and reload it by executing:
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
# \q
$ su - <original_user_name>
```

Also, you need to change the authentication method from peer to md5.      
           
Open `/etc/postgresql/9.3/main/pg_hba.conf` with read and write privilege, and find the following line:
```
local   all             all                                     peer
```
Replace peer to md5 and save the file:
```
local   all             all                                     md5
```
Finally, execute restart the PostgreSQL service:
```
sudo service postgresql restart
```
### 1. 3 Framework Setup
Switch terminal's current directory to the unzipped framework folder and execute run.py:  
```
$ cd <path_to_framework>/ActiveCrowd
$ python run.py
```  
Then you can access the framework on any browser. The first launch of the framework require a simple setup operation. First you need to provide database name, 

database user and database user password (as created in 1. 2):   
     
![Framework first launch database config](http://i.imgur.com/6XtDAWJ.png)
        
Secondly, you need to provide the AWS Key and AWS Secert Key of your Amazon account that is going to use the Amazon Mechanical Turk services. It is suggested to provide these value in this setup stage as a framework-wide default value so you don't need to configure it for each project one by one. Yet, you can leave it blank for now and modify later.
 
![Framework first launch mturk config](http://i.imgur.com/zzQpOI1.png)

To create a MTurk Requester account, please go to either of the following links:       
https://requester.mturk.com/developer      

To obtain your AWS Key and AWS Secert Key for MTurk services:         
          
1. Go to: https://console.aws.amazon.com/iam/home?region=us-east-1#security_credential    
2. Expand the "Access Keys" section and click "Create New Access Key"         
3. Click "Show Access Key" and note down the keys     
           
_*Since MTurk doesn't support IAM user, you must use these root keys. Please keep these two keys very secretly!_     

