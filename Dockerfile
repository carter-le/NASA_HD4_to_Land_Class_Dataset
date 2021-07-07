## docker build . -t pygdal
## docker run -it --rm -p 8000:8888 -v "${PWD}/projects:/projects" pygdal
## jupyter lab --allow-root --ip 0.0.0.0


#### Use latest Ubuntu LTS release as the base
FROM ubuntu:18.04
ARG DEBIAN_FRONTEND=noninteractive
# Update base container install
RUN apt-get update

# Install GDAL dependencies
RUN apt-get install -y python3-pip libgdal-dev locales python-zmq build-essential manpages-dev
RUN locale-gen en_US.UTF-8

# Ensure locales configured correctly
RUN locale-gen en_US.UTF-8
ENV LC_ALL='en_US.utf8'

# Set python aliases for python3
RUN echo 'alias python=python3' >> ~/.bashrc
RUN echo 'alias pip=pip3' >> ~/.bashrc

# Update C env vars so compiler can find gdal
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

#Install Shapely
RUN pip3 install shapely
# Install jupyterlab 
RUN pip3 install jupyterlab
RUN apt-get update &&\
    apt-get install -y binutils libproj-dev gdal-bin
# This will install latest version of GDAL
RUN pip3 install GDAL==2.2.3
RUN pip3 install pymysql
RUN pip3 install Pillow
RUN pip3 install pyshp
RUN pip3 install geomet

EXPOSE 8888
EXPOSE 8000

# Make a project directory and set it as the working directory 
RUN mkdir /projects
WORKDIR /projects



