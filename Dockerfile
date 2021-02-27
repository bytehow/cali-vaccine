FROM python:alpine
COPY requirements.txt .
RUN pip install requests colorama
COPY appointments.py .
CMD python -u appointments.py
