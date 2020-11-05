FROM python:3.8
RUN pip install -U pip wheel
ADD ./be/requirements.txt /opt/diaas/be/requirements.txt
RUN pip install -r /opt/diaas/be/requirements.txt
ADD ./be/ /opt/diaas/be/
ADD ./ops/ /opt/diaas/ops/

ENV PYTHONPATH=/opt/diaas/be/src/
ENV FLASK_APP=diaas.app

ENTRYPOINT ["/opt/diaas/ops/lcl/be.entry-point"]
CMD flask run -h 0.0.0.0 -p 8080
