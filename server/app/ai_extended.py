import os
from dotenv import load_dotenv
from app.internal.ai import AI

from app.internal.prompt import RULES_TEXT

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL") or "gpt-3.5-turbo-1106"

class AIExtended(AI):
 
    async def rephrase_text(self, claim: str, wider_context: str) -> str:
        """
        Rephrases the given text (usually a claim) into a coherent format.
        Returns: Returns replacement text and errors if any in a JSON format.
        TODO :: Address model token limit.
        """
        if not claim or not claim.strip():
            raise ValueError("Claim text cannot be empty")
        
        system_prompt = f"""
            You are working on the "Claims" section of a patent document.

                Here is a description of a patent claim:

                A patent is a legal document that gives an inventor the right to exclude others from practicing an
                invention.

                The claims are the most important section of a patent. The claims define the scope of protection provided by the patent and are the legally operative part of a patent application. The claims must be clear and concise, must be supported by the detailed description, and must be written in a particular format. 

                For example, below is a sample claim.
                An apparatus, comprising:
                - a pencil having an elongated structure with two ends and a center therebetween;
                - an eraser attached to one end of the pencil; and
                - a light attached to the center of the pencil.

                Here are the rules you should check for: {RULES_TEXT}

                Your job is to rewrite the specified text considering a wider context. Only rewrite the specified text. Your response should only contain the text that will directly replace the original text. 

                Respond in valid JSON format:
                {{
                    "result": {{
                        "replacement": "<rewritten_text>",
                        "error": "<short_description_if_no_replacement_is_generated>"
                    }}
                }}

                Return the Original text if you think no modifications are required on the original text.
                If no replacement is generated, then fill the error field with a short description of why no response is being generated. For example, if you don't have enough context from the input, then leave the "replacement" field empty and fill the "error" field with a short description like "need_additional_context" or "incomplete_input"

                Do NOT leave out any information from the original text. The rephrased claim should contain all the information in the original text.

                If you receive an HTML document, you MUST return an error.
                """
        
        user_prompt = f"""
                Wider Context:
                "{wider_context}"

                Text to Modify:
                "{claim}"
        """


        response = await self._client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=False,
        )

        if not response:
            raise ValueError("AI returned empty response")

        return response.choices[0].message.content.strip()

  
    async def analyze_document(self, document_content: str) -> str:
        """
        Analyzes the complete patent document and provides score + high-level suggestions.
        Returns: Returns replacement text and errors if any in a JSON format.
        """

        system_prompt = f"""
            You are a patent attorney working on the "Claims" section of a patent document.

                Here is a description of a patent claim:

                A patent is a legal document that gives an inventor the right to exclude others from practicing an invention.

                The claims are the most important section of a patent. The claims define the scope of protection provided by the patent and are the legally operative part of a patent application. The claims must be clear and concise, must be supported by the detailed description, and must be written in a particular format. 

                For example, below is a sample claim.
                An apparatus, comprising:
                - a pencil having an elongated structure with two ends and a center therebetween;
                - an eraser attached to one end of the pencil; and
                - a light attached to the center of the pencil.

                Here are the rules you should check for: {RULES_TEXT}

                As a Patent attorney, your job is to review the document at a high level and provide crucial information that could result in any office actions or even potential rejection of patent.
                - List a short description on potential areas that could lead to office actions or potential rejection of patent.  
                - Score the document out of 100 based on the rules provided and problematic areas.

                Respond in valid JSON format:
                {{
                    "result": {{
                        "score": "<score out of 100>",
                        "problems": [
                            "<possible_office_action_and_reason>",
                            "<possible_office_action_and_reason>"
                        ]
                    }}
                }}

                Return an empty list in "problems" section if the document is good enough.

                If you receive an HTML document, you MUST return an error.
                """
        
        user_prompt = f"""
                Document Content:\n 
                {document_content}
        """


        response = await self._client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=False,
        )

        return response.choices[0].message.content.strip()

       

    async def send_prompt(
    self, prompt:str
    ) -> str:
        """
        A generic function to send any prompt and receive text from AI.
        Returns: The complete text generated for the given prompt.
        """
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=False,
        )

        return response.choices[0].message.content.strip()


def get_ai(
    model: str | None = OPENAI_MODEL,
    api_key: str | None = OPENAI_API_KEY,
) -> AIExtended:
    if not api_key or not model:
        raise ValueError("Both API key and model need to be set")
    return AIExtended(api_key, model)