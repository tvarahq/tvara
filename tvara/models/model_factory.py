from tvara.models.gemini import GoogleGeminiModel
from tvara.models.supported_models import gemini_supported

class ModelFactory:
    """
    Factory class to create model instances based on the model name.
    """
    _model_map = {
        model_name: GoogleGeminiModel for model_name in gemini_supported
    }
    
    @staticmethod
    def create_model(model_name: str, api_key: str):
        """
        Creates an instance of the model based on the model name.
        Args:
            model_name (str): The name of the model to create.
            api_key (str): The API key for the model.
        Returns:
            The model instance.
        Raises:
            ValueError: If the model name is not supported.
        """
        model_cls = ModelFactory._model_map.get(model_name)
        if not model_cls:
            raise ValueError(f"Model '{model_name}' is not supported.")
        return model_cls(model_name=model_name, api_key=api_key)