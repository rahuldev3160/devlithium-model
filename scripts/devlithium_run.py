"""Devlithium launcher."""
import os, sys
WEB = "/Users/rahulsingh/Desktop/Claude Projects/Devlithium Model/web"
os.chdir(WEB)
sys.path.insert(0, WEB)
import uvicorn
uvicorn.run("app:app", host="0.0.0.0", port=4200)
