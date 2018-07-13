FROM python:3.6

RUN git clone https://github.com/grafuls/disruption_generator

WORKDIR disruption_generator
RUN pip install pipenv && pipenv install --dev && pipenv run python setup.py install
VOLUME /share

ENTRYPOINT pipenv run disruption_generator

