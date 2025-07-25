from tvara.models.gemini import GoogleGeminiModel

class ModelFactory:
    """
    Factory class to create model instances based on the model name.
    """
    
    @staticmethod
    def create_model(model_name: str, api_key: str) -> GoogleGeminiModel:
        """
        Creates an instance of the GoogleGeminiModel.
        
        Args:
            model_name (str): The name of the model to create.
            api_key (str): The API key for the model.
        
        Returns:
            GoogleGeminiModel: An instance of the GoogleGeminiModel.
        """
        return GoogleGeminiModel(model_name=model_name, api_key=api_key)