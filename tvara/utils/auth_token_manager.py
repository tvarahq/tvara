import os
import json
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AuthTokenManager:
    """Manages authentication tokens for non-interactive deployments."""
    
    def __init__(self, cache_dir: str = "./cache"):
        """
        Initialize the authentication token manager.
        
        Args:
            cache_dir (str): Directory to store token cache files
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # Define auth schemes for different toolkits
        self.toolkit_auth_schemes = {
            "github": "BEARER_TOKEN",
            "slack": "BEARER_TOKEN", 
            "notion": "BEARER_TOKEN",
            "google": "OAUTH2",  # Usually OAuth2, but can be API_KEY for some services
            "linear": "BEARER_TOKEN",
            "jira": "BEARER_TOKEN",
            "discord": "BEARER_TOKEN",
            "twitter": "BEARER_TOKEN",
            "instagram": "BEARER_TOKEN",
            "youtube": "BEARER_TOKEN"
        }
        
    def get_toolkit_token(self, toolkit: str) -> Optional[str]:
        """
        Get authentication token for a toolkit from environment variables.
        
        Looks for tokens in the following formats:
        - COMPOSIO_AUTH_{TOOLKIT_NAME}
        - COMPOSIO_{TOOLKIT_NAME}_TOKEN
        - {TOOLKIT_NAME}_TOKEN
        
        Args:
            toolkit (str): Name of the toolkit
            
        Returns:
            Optional[str]: Authentication token if found, None otherwise
        """
        toolkit_upper = toolkit.upper().replace("-", "_").replace(" ", "_")
        
        # Try different environment variable patterns
        env_patterns = [
            f"COMPOSIO_AUTH_{toolkit_upper}",
            f"COMPOSIO_{toolkit_upper}_TOKEN", 
            f"{toolkit_upper}_TOKEN",
            f"COMPOSIO_AUTH_{toolkit_upper.lower()}",
            f"COMPOSIO_{toolkit_upper.lower()}_TOKEN",
            f"{toolkit_upper.lower()}_TOKEN"
        ]
        
        for pattern in env_patterns:
            token = os.getenv(pattern)
            if token:
                logger.info(f"Found authentication token for {toolkit} in {pattern}")
                return token
                
        return None
    
    def has_toolkit_token(self, toolkit: str) -> bool:
        """
        Check if authentication token exists for a toolkit.
        
        Args:
            toolkit (str): Name of the toolkit
            
        Returns:
            bool: True if token exists, False otherwise
        """
        return self.get_toolkit_token(toolkit) is not None
    
    def get_missing_tokens(self, toolkits: List[str], no_auth_toolkits: List[str]) -> List[str]:
        """
        Get list of toolkits that require tokens but don't have them configured.
        
        Args:
            toolkits (List[str]): List of toolkit names
            no_auth_toolkits (List[str]): List of toolkits that don't require auth
            
        Returns:
            List[str]: List of toolkit names missing tokens
        """
        missing = []
        for toolkit in toolkits:
            if toolkit.upper() not in [t.upper() for t in no_auth_toolkits]:
                if not self.has_toolkit_token(toolkit):
                    missing.append(toolkit)
        return missing
    
    def get_toolkit_auth_scheme(self, toolkit: str) -> str:
        """
        Get the appropriate auth scheme for a toolkit.
        
        Args:
            toolkit (str): Name of the toolkit
            
        Returns:
            str: Auth scheme (BEARER_TOKEN, API_KEY, OAUTH2, etc.)
        """
        return self.toolkit_auth_schemes.get(toolkit.lower(), "BEARER_TOKEN")
    
    def create_auth_config(self, composio_client, toolkit: str, token: str) -> Optional[str]:
        """
        Create an auth config for a toolkit using the provided token.
        
        Args:
            composio_client: Composio client instance
            toolkit (str): Name of the toolkit
            token (str): Authentication token
            
        Returns:
            Optional[str]: Auth config ID if successful, None otherwise
        """
        try:
            auth_scheme = self.get_toolkit_auth_scheme(toolkit)
            toolkit_lower = toolkit.lower()
            
            # Prepare auth config options based on scheme
            if auth_scheme == "BEARER_TOKEN":
                options = {
                    "name": f"tvara-{toolkit_lower}-{datetime.now().strftime('%Y%m%d')}",
                    "auth_scheme": auth_scheme,
                    "credentials": {
                        "token": token
                    }
                }
            elif auth_scheme == "API_KEY":
                options = {
                    "name": f"tvara-{toolkit_lower}-{datetime.now().strftime('%Y%m%d')}",
                    "auth_scheme": auth_scheme,
                    "credentials": {
                        "api_key": token
                    }
                }
            else:
                logger.warning(f"Unsupported auth scheme {auth_scheme} for toolkit {toolkit}")
                return None
                
            # Create the auth config
            config = composio_client.auth_configs.create(
                toolkit=toolkit_lower,
                options=options
            )
            
            auth_config_id = config.id if hasattr(config, 'id') else getattr(config, 'nanoid', None)
            if not auth_config_id:
                logger.error(f"Failed to get auth config ID for {toolkit}")
                return None
                
            logger.info(f"Created auth config for {toolkit}: {auth_config_id}")
            return auth_config_id
            
        except Exception as e:
            logger.error(f"Failed to create auth config for {toolkit}: {e}")
            return None
    
    def create_connected_account(self, composio_client, user_id: str, auth_config_id: str, toolkit: str) -> bool:
        """
        Create and activate a connected account using the auth config.
        
        Args:
            composio_client: Composio client instance
            user_id (str): User ID
            auth_config_id (str): Auth config ID
            toolkit (str): Toolkit name
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Initiate the connection
            connection_request = composio_client.toolkits.connected_accounts.initiate(
                user_id=user_id,
                auth_config_id=auth_config_id
            )
            
            # Wait for connection to be established
            if hasattr(connection_request, 'id'):
                connection_id = connection_request.id
                connected_account = composio_client.toolkits.connected_accounts.wait_for_connection(
                    id=connection_id,
                    timeout=30.0  # 30 second timeout
                )
                
                # Check if connection is active
                if hasattr(connected_account, 'status') and connected_account.status == 'ACTIVE':
                    logger.info(f"Successfully connected to {toolkit}")
                    return True
                else:
                    logger.error(f"Connection to {toolkit} not active: {getattr(connected_account, 'status', 'unknown')}")
                    return False
            else:
                logger.error(f"Failed to get connection ID for {toolkit}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to create connected account for {toolkit}: {e}")
            return False
    
    def get_auth_instructions(self, toolkit: str) -> str:
        """
        Get authentication setup instructions for a toolkit.
        
        Args:
            toolkit (str): Name of the toolkit
            
        Returns:
            str: Instructions for setting up authentication
        """
        toolkit_upper = toolkit.upper().replace("-", "_").replace(" ", "_")
        
        instructions = f"""
Authentication Setup for {toolkit}:

Option 1 - Environment Variable:
  Set one of these environment variables:
  export COMPOSIO_AUTH_{toolkit_upper}="your_token_here"
  export COMPOSIO_{toolkit_upper}_TOKEN="your_token_here"
  export {toolkit_upper}_TOKEN="your_token_here"

Option 2 - Get Token Interactively:
  Run authentication in interactive mode first:
  python -c "
from tvara.core import Agent
import os
agent = Agent(
    name='Auth Helper',
    model='gemini-2.5-flash',
    api_key=os.getenv('MODEL_API_KEY'),
    composio_api_key=os.getenv('COMPOSIO_API_KEY'),
    composio_toolkits=['{toolkit}']
)
print('Authentication completed and cached')
  "
  
Then check your ~/.composio directory for tokens that can be copied to environment variables.

For more details, visit: https://docs.composio.dev/introduction/foundations/components/entity/entity-guide
"""
        return instructions.strip()
    
    def validate_environment_setup(self, toolkits: List[str], no_auth_toolkits: List[str]) -> Dict:
        """
        Validate that all required authentication is properly configured.
        
        Args:
            toolkits (List[str]): List of toolkit names
            no_auth_toolkits (List[str]): List of toolkits that don't require auth
            
        Returns:
            Dict: Validation results with missing tokens and instructions
        """
        missing_tokens = self.get_missing_tokens(toolkits, no_auth_toolkits)
        
        result = {
            "valid": len(missing_tokens) == 0,
            "missing_tokens": missing_tokens,
            "configured_toolkits": [t for t in toolkits if t not in missing_tokens],
            "no_auth_toolkits": [t for t in toolkits if t.upper() in [n.upper() for n in no_auth_toolkits]]
        }
        
        if missing_tokens:
            result["instructions"] = "\n\n".join([
                self.get_auth_instructions(toolkit) for toolkit in missing_tokens
            ])
            
        return result