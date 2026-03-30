#!/bin/bash
# Install Microsoft ODBC Driver 18 for SQL Server on Streamlit Cloud
# Streamlit Cloud currently runs Ubuntu 22.04

if ! command -v sqlcmd &> /dev/null; then
    curl -sSL https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
    curl -sSL https://packages.microsoft.com/config/ubuntu/22.04/prod.list \
        > /etc/apt/sources.list.d/mssql-release.list
    apt-get update -qq
    ACCEPT_EULA=Y apt-get install -y -qq msodbcsql18 msodbcsql17 2>/dev/null || \
    ACCEPT_EULA=Y apt-get install -y -qq msodbcsql17 2>/dev/null || true
fi
