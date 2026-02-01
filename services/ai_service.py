import os
import requests
import json
import time

DEFAULT_PROMPT = """
Role: You are an expert B2B social seller.
Task: Write a single, punchy ice-breaker sentence (max 180 chars).

CRITICAL RULES:
1. **Language**: ALWAYS WRITE IN ENGLISH. Even if the profile is French.
2. **Formatting**: 
   - NO quotation marks.
   - NO DASHES of any kind (-, –, —). User commas instead.
   - NO headers.
3. **Content**: 
   - NO resume summaries.
   - Casual, punchy, and FRIENDLY.
   - NO emojis.
   - Start with "Hi [First Name]," or "Hey [First Name],"

Desired Example: "Hey Muriel, managing €1B P&L while keeping that startup mindset, is that your superpower?"
Bad Example: "Hello, I see you moved from..."

Info Prospect:
Name: {name}
Headline: {headline}
Summary: {summary}
Experience: {experience}

Message (Raw text only):
"""

class AIService:
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_KEY')
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "anthropic/claude-sonnet-4.5" 

    def generate_icebreaker(self, prospect_data, prompt_template=None):
        """
        Génère un message d'accroche personnalisé.
        """
        if not self.api_key:
            return "Error: OPENROUTER_KEY not found in .env"

        final_prompt = prompt_template if prompt_template else DEFAULT_PROMPT
        
        # Formatting the prompt with safe defaults
        formatted_prompt = final_prompt.format(
            name=prospect_data.get('name') or '',
            headline=prospect_data.get('headline') or '',
            summary=(prospect_data.get('summary') or '')[:500], # Limit context size
            experience=str(prospect_data.get('experience') or '')[:500]
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://linkedin-mvp.local", # Required by OpenRouter
            "X-Title": "LinkedIn MVP",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,

            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": formatted_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 150
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content'].strip()
                    
                    # Post-processing to enforce user rules strictly
                    # 1. Remove ANY surrounding quotation marks (single or double)
                    content = content.strip('"').strip("'")
                    
                    # 2. Replace all forms of dashes with commas
                    # Em-dash, En-dash, standard dash surrounded by spaces
                    content = content.replace("—", ", ").replace("–", ", ").replace(" - ", ", ")
                    
                    # 3. Final cleanup of whitespace
                    content = content.strip()
                    
                    return content
                else:
                    return "Error: Empty response from AI"
            else:
                return f"Error: API returned {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"Error calling AI: {str(e)}"
