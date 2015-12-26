#!/bin/bash

cd tasa_website
gunicorn tasa_website:app
