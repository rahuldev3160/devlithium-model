"""Devlithium launcher — sets working directory then starts uvicorn."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())
import uvicorn
uvicorn.run("app:app", host="0.0.0.0", port=4200)
