# DAS Web backend on Django README

# Install

## Install python3, pip
`pacman -S python python-pip`

## Install virtualenv
`pip3 install virtualenv`

## Init virtual environment
```
mkdir venv
python3 -m venv venv/
source venv/bin/activate
```

### Install requirements
`pip3 install -r requirements/requirements.txt`

## Generate new secret key
`python3 das/management/commands/gen_secret_key.py`  

## Copy settings files and set your secret key, database and path settings:
```
cp das/dev.env{.example,}
cp das/prod.env{.example,}
```  

