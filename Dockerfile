FROM python:alpine
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY .tweetrc .
COPY tweet.py .
COPY appointments.py .
CMD python -u appointments.py
