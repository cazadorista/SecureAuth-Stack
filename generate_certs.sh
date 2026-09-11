#!/bin/bash
mkcert -cert-file certs/local-cert.pem -key-file certs/local-key.pem localhost auth.localhost api.localhost traefik.localhost 127.0.0.1 ::1