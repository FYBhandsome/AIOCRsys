#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests

print('检查Visual Model服务...')
try:
    r = requests.get('http://localhost:8001/api/v1/health', timeout=3)
    print(f'Visual Model: {r.status_code} - {r.text}')
except Exception as e:
    print(f'Visual Model不可用: {e}')

print('检查RAG服务...')
try:
    r = requests.get('http://localhost:8000/health', timeout=3)
    print(f'RAG: {r.status_code} - {r.text}')
except Exception as e:
    print(f'RAG不可用: {e}')
