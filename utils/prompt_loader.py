import os
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class PromptLoader:
    """
    Utility class for loading prompts from files.
    Provides caching and error handling for prompt file operations.
    """
    
    def __init__(self, prompts_dir: Optional[str] = None):
        """
        Initialize the PromptLoader.
        
        Args:
            prompts_dir: Optional custom prompts directory path.
                        If None, will use default prompts directory relative to project root.
        """
        self.prompts_dir = prompts_dir
        self._cache = {}  # Simple in-memory cache for loaded prompts
    
    def _get_prompts_directory(self) -> str:
        """
        Get the prompts directory path.
        
        Returns:
            str: Path to the prompts directory
        """
        if self.prompts_dir:
            return self.prompts_dir
        
        # Get the directory of the current file (utils/prompt_loader.py)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Navigate to the project root and then to prompts directory
        project_root = os.path.dirname(current_dir)
        return os.path.join(project_root, "prompts")
    
    def load_prompt(self, filename: str, use_cache: bool = True) -> str:
        """
        Load a prompt from a file.
        
        Args:
            filename: Name of the prompt file (e.g., 'pro_prompt.txt')
            use_cache: Whether to use cached version if available
            
        Returns:
            str: The content of the prompt file
            
        Raises:
            FileNotFoundError: If the prompt file is not found
            Exception: If there's an error reading the file
        """
        # Check cache first
        if use_cache and filename in self._cache:
            logger.debug(f"Loading prompt '{filename}' from cache")
            return self._cache[filename]
        
        prompts_dir = self._get_prompts_directory()
        prompt_file_path = os.path.join(prompts_dir, filename)
        
        try:
            with open(prompt_file_path, 'r', encoding='utf-8') as file:
                content = file.read().strip()
                
            # Cache the content
            if use_cache:
                self._cache[filename] = content
                
            logger.info(f"Successfully loaded prompt from: {prompt_file_path}")
            return content
            
        except FileNotFoundError:
            error_msg = f"Prompt file not found: {prompt_file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        except Exception as e:
            error_msg = f"Error reading prompt file '{prompt_file_path}': {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def load_pro_prompt(self, use_cache: bool = True) -> str:
        """
        Load the pro prompt specifically.
        
        Args:
            use_cache: Whether to use cached version if available
            
        Returns:
            str: The content of the pro prompt file
        """
        return self.load_prompt("pro_prompt.txt", use_cache)
    
    def clear_cache(self, filename: Optional[str] = None) -> None:
        """
        Clear the prompt cache.
        
        Args:
            filename: Specific file to remove from cache. If None, clears all cache.
        """
        if filename:
            self._cache.pop(filename, None)
            logger.debug(f"Cleared cache for prompt: {filename}")
        else:
            self._cache.clear()
            logger.debug("Cleared all prompt cache")
    
    def list_available_prompts(self) -> list[str]:
        """
        List all available prompt files in the prompts directory.
        
        Returns:
            list[str]: List of prompt filenames
        """
        prompts_dir = self._get_prompts_directory()
        
        try:
            if not os.path.exists(prompts_dir):
                logger.warning(f"Prompts directory does not exist: {prompts_dir}")
                return []
            
            prompt_files = []
            for file in os.listdir(prompts_dir):
                if file.endswith('.txt') or file.endswith('.md'):
                    prompt_files.append(file)
            
            logger.debug(f"Found {len(prompt_files)} prompt files in {prompts_dir}")
            return sorted(prompt_files)
            
        except Exception as e:
            logger.error(f"Error listing prompt files: {e}")
            return []
    
    def prompt_exists(self, filename: str) -> bool:
        """
        Check if a prompt file exists.
        
        Args:
            filename: Name of the prompt file to check
            
        Returns:
            bool: True if the file exists, False otherwise
        """
        prompts_dir = self._get_prompts_directory()
        prompt_file_path = os.path.join(prompts_dir, filename)
        return os.path.exists(prompt_file_path)


# Convenience functions for backward compatibility and easy usage
def load_prompt(filename: str, prompts_dir: Optional[str] = None, use_cache: bool = True) -> str:
    """
    Convenience function to load a prompt file.
    
    Args:
        filename: Name of the prompt file
        prompts_dir: Optional custom prompts directory
        use_cache: Whether to use caching
        
    Returns:
        str: The content of the prompt file
    """
    loader = PromptLoader(prompts_dir)
    return loader.load_prompt(filename, use_cache)

def load_pro_prompt(prompts_dir: Optional[str] = None, use_cache: bool = True) -> str:
    """
    Convenience function to load the pro prompt.
    
    Args:
        prompts_dir: Optional custom prompts directory
        use_cache: Whether to use caching
        
    Returns:
        str: The content of the pro prompt file
    """
    loader = PromptLoader(prompts_dir)
    return loader.load_pro_prompt(use_cache)

def load_lazy_prompt(prompts_dir: Optional[str] = None, use_cache: bool = True) -> str:
    """
    Convenience function to load the lazy prompt.
    
    Args:
        prompts_dir: Optional custom prompts directory
        use_cache: Whether to use caching
        
    Returns:
        str: The content of the lazy prompt file
    """
    loader = PromptLoader(prompts_dir)
    return loader.load_prompt("lazy_prompt.txt", use_cache)
