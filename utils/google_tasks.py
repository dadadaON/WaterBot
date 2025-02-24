from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
from pathlib import Path
from typing import Optional, Dict, Any
import asyncio
from functools import partial
from datetime import datetime

from config import GOOGLE_CREDENTIALS_FILE, TOKEN_PICKLE_FILE, GOOGLE_API_SCOPES as SCOPES
from utils.logger import logger

class GoogleTasksManager:
    def __init__(self):
        self.creds = None
        self.service = None
        logger.info("GoogleTasksManager initialized")
    
    async def authenticate(self):
        """Асинхронна аутентифікація"""
        try:
            logger.info("Starting Google authentication")
            logger.debug(f"Using credentials file: {GOOGLE_CREDENTIALS_FILE}")
            logger.debug(f"Using token file: {TOKEN_PICKLE_FILE}")
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._authenticate_sync)
            logger.info("Google authentication completed successfully")
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            logger.exception("Full authentication error traceback:")
            raise
    
    def _authenticate_sync(self):
        """Синхронна версія аутентифікації"""
        try:
            logger.debug("Starting synchronous authentication")
            if Path(TOKEN_PICKLE_FILE).exists():
                logger.debug("Loading credentials from pickle file")
                with open(TOKEN_PICKLE_FILE, 'rb') as token:
                    self.creds = pickle.load(token)
            
            if not self.creds or not self.creds.valid:
                logger.debug("Credentials are invalid or missing")
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    logger.info("Refreshing expired credentials")
                    self.creds.refresh(Request())
                else:
                    logger.info("Getting new credentials")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        GOOGLE_CREDENTIALS_FILE, 
                        SCOPES,
                        redirect_uri='http://localhost:8080'
                    )
                    self.creds = flow.run_local_server(
                        port=8080,
                        access_type='offline',
                        include_granted_scopes='true'
                    )
                
                logger.debug("Saving credentials to pickle file")
                with open(TOKEN_PICKLE_FILE, 'wb') as token:
                    pickle.dump(self.creds, token)
            
            self.service = build('tasks', 'v1', credentials=self.creds)
            logger.info("Google Tasks service initialized successfully")
        except Exception as e:
            logger.error(f"Error in _authenticate_sync: {str(e)}")
            logger.exception("Authentication error details:")
            raise
    
    async def create_task_list(self, title: str) -> Dict[str, Any]:
        try:
            logger.info(f"Attempting to create new task list: {title}")
            logger.debug(f"Task list data: {{'title': {title}}}")
            
            if not self.service:
                logger.error("Google Tasks service is not initialized")
                raise ValueError("Service not initialized. Please authenticate first.")
            
            task_list = {'title': title}
            
            loop = asyncio.get_event_loop()
            create_list = partial(self.service.tasklists().insert(
                body=task_list
            ).execute)
            
            logger.debug("Executing API call to create task list")
            result = await loop.run_in_executor(None, create_list)
            logger.info(f"Task list created successfully with ID: {result.get('id')}")
            logger.debug(f"Full task list response: {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to create task list: {str(e)}")
            logger.exception("Full error traceback:")
            raise

    async def create_task(self, list_id: str, title: str, notes: Optional[str] = None, due: Optional[str] = None) -> Dict[str, Any]:
        try:
            logger.info(f"Creating new task: {title}")
            task = {'title': title}
            if notes:
                task['notes'] = notes
            if due:
                due_date = datetime.strptime(due, "%Y-%m-%d").isoformat() + 'Z'
                task['due'] = due_date
            
            loop = asyncio.get_event_loop()
            create_task = partial(self.service.tasks().insert(
                tasklist=list_id,
                body=task
            ).execute)
            
            result = await loop.run_in_executor(None, create_task)
            logger.info(f"Task created successfully with ID: {result.get('id')}")
            return result
        except Exception as e:
            logger.error(f"Failed to create task: {str(e)}")
            raise
    
    async def get_tasks(self, max_results: int = 10) -> list:
        """Отримує список завдань"""
        try:
            logger.info(f"Fetching tasks (max {max_results})")
            loop = asyncio.get_event_loop()
            get_tasks = partial(self.service.tasks().list(
                tasklist='@default',
                maxResults=max_results
            ).execute)
            
            result = await loop.run_in_executor(None, get_tasks)
            logger.info(f"Successfully fetched {len(result.get('items', []))} tasks")
            return result
        except Exception as e:
            logger.error(f"Failed to fetch tasks: {str(e)}")
            raise

    async def add_task(self, title, description, list_id):
        # Логіка для додавання завдання у Google Tasks
        pass 

    async def test_connection(self):
        """Тестує з'єднання з Google Tasks API"""
        try:
            logger.info("Testing Google Tasks connection")
            if not self.service:
                await self.authenticate()
            
            # Спробуємо отримати списки завдань
            loop = asyncio.get_event_loop()
            test = partial(self.service.tasklists().list().execute)
            result = await loop.run_in_executor(None, test)
            
            logger.info(f"Connection test successful. Found {len(result.get('items', []))} task lists")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            logger.exception("Test connection error details:")
            return False 