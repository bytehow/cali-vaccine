FROM python:alpine
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY twitter.py .
COPY appointments.py .
CMD python -u appointments.py
