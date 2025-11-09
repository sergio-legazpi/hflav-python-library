# hflav-python-library

To run this project you firstly must create a virtual environment and install all the dependencies inside:

1. `python -m venv .venv`
2. `source .venv/bin/activate`
3. `pip install -r requirements.txt`

To obtain the last schema code definition

1. `docker build -t 'quicktype' .`

2. 
```
sudo docker run --rm   -v "$(pwd)":/workdir -w /workdir   quicktype   --lang python   --src-lang schema   --all-properties-optional   -o hflav_z
enodo/hflav_schema.py   HFLAV.schema
```