FROM node:15-buster
ADD ./fe/package.json /opt/diaas/fe/package.json
ADD ./fe/package-lock.json /opt/diaas/fe/package-lock.json
WORKDIR /opt/diaas/fe/
RUN npm install

RUN echo "Must be volume mounted" > /opt/diaas/fe/jsconfig.json
ADD ./ops/ /opt/diaas/ops/
ENTRYPOINT ["/opt/diaas/ops/lcl/fe.entry-point"]
CMD ["npm", "run", "start"]
