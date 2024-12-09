FROM harbor.emea.ocp.int.kn/dockerhub/library/python:3.12.3
WORKDIR /usr/vvapi
COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONPATH "${PYTHONPATH}:/app"
CMD [ "python", "./app/main.py" ]
