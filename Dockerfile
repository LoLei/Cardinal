FROM python:3.9

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN find plugins -type f -name requirements.txt -exec pip install --no-cache-dir -r {} \;

ENTRYPOINT [ "python", "./cardinal.py" ]
