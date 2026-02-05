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

    def analyze_batch_signals(self, prospects_list):
        """
        Analyse un lot de prospects pour détecter des "Signal Tags".
        prospects_list: liste de dicts {'id': 1, 'headline': '...', 'about': '...'}
        Retourne: dict { str(id): ['Tag1', 'Tag2'] }
        """
        # print(f"DEBUG INPUT: {type(prospects_list)} - {prospects_list}") # DEBUG
        if not self.api_key:
            print("Error: OPENROUTER_KEY not found")
            return {}

        prompt = """
Role: You are an expert B2B analyst.
Task: Analyze the following list of LinkedIn profiles and identify "Signal Tags".

Signal Definitions:
- "Platform/DevEx initiatives": Mentions Platform Engineering, IDP, Developer Experience, DevEX, DX.
- "AI coding mentions": Mentions AI coding agents, Copilot, Cursor, LLM for code, autonomous coding.
- "scaling/hiring": Mentions "scaling", "hypergrowth", "hiring", "growing", "recruiting".
- "productivity investment": Mentions "engineering productivity", "developer productivity", "DORA metrics", "SPACE framework".
- "refactor/tech debt narratives": Mentions "tech debt", "refactoring", "legacy code", "modernization".

Input:
{prospects_json}

Each profile contains: id, headline, summary (bio), and skills (list).

Output Rules:
- Return ONLY valid JSON.
- Format: {{ "id": ["tag_name1", "tag_name2"] }}
- Use EXACT tag names from the list above.
"""
        
        # Prepare clean JSON input for AI
        clean_input = []
        for p in prospects_list:
            clean_input.append({
                'id': str(p['id']),
                'headline': (p.get('headline') or '')[:300],
                'about': (p.get('summary') or '')[:500]
            })
            
        final_prompt = prompt.format(prospects_json=json.dumps(clean_input))

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://linkedin-mvp.local",
            "X-Title": "LinkedIn MVP",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a JSON-only response bot."},
                {"role": "user", "content": final_prompt}
            ],
            "temperature": 0.0, # Deterministic
            "response_format": { "type": "json_object" } # Force JSON if supported, else prompt does it
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                data=json.dumps(payload),
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                # print(f"DEBUG AI RESP: {content}") # DEBUG
                
                # Cleanup Markdown Code Blocks
                content = content.replace("```json", "").replace("```", "").strip()
                
                # Parse JSON
                return json.loads(content)
            else:
                print(f"AI Error: {response.text}")
                return {}
        except Exception as e:
            print(f"Batch AI Error: {e}")
            return {}
