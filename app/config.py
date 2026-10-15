import os
from dotenv import load_dotenv
load_dotenv()
MESH_MODEL = os.getenv('MESH_MODEL', 'openai/gpt-4o')
DATABASE_PATH = os.getenv('DATABASE_PATH', 'deepdive.sqlite3')
MAX_RESEARCH_ROUNDS = max(1, min(4, int(os.getenv('MAX_RESEARCH_ROUNDS', '2'))))
SEARCH_RESULTS_PER_QUERY = max(1, min(8, int(os.getenv('SEARCH_RESULTS_PER_QUERY', '4'))))
