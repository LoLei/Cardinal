FROM python:3.9

WORKDIR /usr/src/app

COPY . .

RUN apt-get update -y
RUN apt-get upgrade -y

# Get Ubuntu packages
RUN apt-get install -y build-essential curl
RUN apt-get install libffi-dev libssl-dev python-dev -y
 
# Get Rust
RUN curl https://sh.rustup.rs -sSf | bash -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

RUN pip install --upgrade pip
RUN pip install setuptools 
RUN pip install cryptography

RUN pip install --no-cache-dir -r requirements.txt
RUN find plugins -type f -name requirements.txt -exec pip install --no-cache-dir -r {} \;

ENTRYPOINT [ "python", "./cardinal.py" ]
