# PetSurveilanceSystem

## Setup

```
//Configure access to port 80
sudo apt install authbind
sudo touch /etc/authbind/byport/80
sudo chmod 777 /etc/authbind/byport/80
```

## Run
```
sudo chmod 7 t.jpg
source venv/bin/activate
authbind --deep python3 app.py
```
