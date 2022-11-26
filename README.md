# Gatekeeper
## Automatic parking lot gates controller simulator
**Using Free OCR API for image to text recognition, with running limitation of 10 times within every 10 minutes.**

**Prerequisites:**

1. **Installing python requirements (after cloning this repo)**
    
    cd gatekeeper

    pip install -r requirements.txt

2. **Installing MySQL server, on Ubuntu:**

    *Installing:*
  
    sudo apt update
  
    sudo apt install mysql-server
  
    sudo systemctl start mysql.service
  
    *Configuring:*
  
    $ sudo mysql
  
    mysql> ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '123123';
  
    mysql> exit
