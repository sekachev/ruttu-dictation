class TextProcessor:
    def __init__(self, config_manager):
        self.config = config_manager

    def process_segment(self, text, is_final=False):
        """
        Main logic for filtering hallucinations and applying commands.
        """
        text_lower = text.lower().strip().rstrip(".")
        
        # 1. Check exclusions
        exclusions = self.config.get("exclusions")
        if text_lower in [e.lower() for e in exclusions]:
            print(f"[DEBUG] Filtered hallucination: {text}")
            return None

        # 2. Check commands
        commands = self.config.get("commands")
        if text_lower in commands:
            return commands[text_lower]

        return text
