# dialogue/modality_handler.py


class DialogueModalityHandler:
    """
    Controls how different modalities affect conversation flow.
    """

    def adjust_response_behavior(self, modality: str, response: dict) -> dict:
        """
        Modifies response based on modality for better dialogue flow.
        """

        if modality == "boolean":
            response["style"] = "short"

        elif modality == "multiple_choice":
            response["style"] = "interactive"

        elif modality == "numeric":
            response["style"] = "explanatory"

        elif modality == "categorical":
            response["style"] = "label_focused"

        else:
            response["style"] = "default"

        return response