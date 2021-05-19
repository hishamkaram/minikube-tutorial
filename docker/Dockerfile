FROM python:3.9.2-slim-buster
LABEL maintainer="AnyManager Dev Team<dev@anymanager.io>"

# environment variables
ENV DEBCONF_NOWARNINGS yes
ENV USER_NAME appuser
ENV APP_DIR app
ENV FULL_DIR /home/${USER_NAME}/${APP_DIR}
ENV PORT 8080
ENV USER_UID 1010
ENV GROUP_GID 1010
ENV SYSTEM_VERSION_COMPAT 1
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PIP_NO_CACHE_DIR 1
ENV PYTHONUNBUFFERED 1

# create non root user
RUN groupadd -g ${USER_UID} ${USER_NAME} && useradd -u ${GROUP_GID} -m -g ${USER_NAME} ${USER_NAME} && mkdir -p ${FULL_DIR}

# change the current path in the contianer
WORKDIR ${FULL_DIR}
COPY requirements.txt requirements.txt
# install python libraries
RUN pip install -r requirements.txt

COPY . .

RUN chown -R ${USER_NAME}:${USER_NAME} ${FULL_DIR} && \
    find ${FULL_DIR} -type f -exec chmod 644 {} \; && \
    find ${FULL_DIR} -type d -exec chmod 755 {} \; && \
    chgrp -R ${USER_NAME} ${FULL_DIR}

# cleanup image
RUN rm -rf ~/.cache/pip && rm -rf /root/.cache
RUN apt autoremove --purge -y && apt autoclean -y && apt-get clean -y
RUN rm -rf /var/lib/apt/lists/* && apt-get clean -y && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
RUN echo "Yes, do as I say!" | apt-get remove --force-yes login && \
    dpkg --remove --force-depends wget
USER ${USER_NAME}

CMD python manage.py runserver 0.0.0.0:${PORT}
