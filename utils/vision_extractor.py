"""
Vision model integration for text extraction.
Supports Qwen3-VL via HuggingFace API and GPT-4 Vision via OpenAI API.
"""
import os
import re
from PIL import Image
from io import BytesIO
import base64

# Try to import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Try to import huggingface_hub for API inference
try:
    from huggingface_hub import InferenceClient
    HF_HUB_AVAILABLE = True
except ImportError:
    HF_HUB_AVAILABLE = False


# Available models for selection
AVAILABLE_MODELS = {
    "Qwen3-VL-8B": {
        "id": "Qwen/Qwen3-VL-8B-Instruct",
        "name": "Qwen3-VL-8B-Instruct",
        "description": "Excellent for handwritten text, diagrams, and scientific content",
        "inference_type": "huggingface"
    },
    "GPT-4-Vision": {
        "id": "gpt-4o",
        "name": "GPT-4 Vision (OpenAI)",
        "description": "Most accurate for complex documents, excellent reasoning",
        "inference_type": "openai"
    }
}


def get_available_models():
    """Return list of available model options for the UI."""
    return list(AVAILABLE_MODELS.keys())


def get_model_info(model_key: str) -> dict:
    """Get model information by key."""
    return AVAILABLE_MODELS.get(model_key, AVAILABLE_MODELS["Qwen3-VL-8B"])


class VisionExtractor:
    """
    Extract text from images using vision-language models.
    Supports Qwen3-VL (HuggingFace) and GPT-4 Vision (OpenAI).
    """
    
    def __init__(self, hf_token: str = None, openai_key: str = None, model_key: str = "Qwen3-VL-8B"):
        """
        Initialize the vision extractor.
        
        Args:
            hf_token: HuggingFace API token (for Qwen models).
            openai_key: OpenAI API key (for GPT-4 Vision).
            model_key: Key for the model to use (from AVAILABLE_MODELS).
        """
        self.hf_token = hf_token or os.environ.get("HF_TOKEN")
        self.openai_key = openai_key or os.environ.get("OPENAI_API_KEY")
        self.model_key = model_key
        self.model_info = get_model_info(model_key)
        self.inference_type = self.model_info.get("inference_type", "huggingface")
        self.client = None
        
        if self.inference_type == "huggingface":
            if not HF_HUB_AVAILABLE:
                raise RuntimeError("huggingface_hub not installed. Run: pip install huggingface_hub")
            self._init_huggingface_client()
        elif self.inference_type == "openai":
            if not OPENAI_AVAILABLE:
                raise RuntimeError("openai not installed. Run: pip install openai")
            if not self.openai_key:
                raise RuntimeError("OpenAI API key required. Set OPENAI_API_KEY in secrets.toml")
            self._init_openai_client()
    
    def _init_huggingface_client(self):
        """Initialize HuggingFace Inference API client."""
        self.client = InferenceClient(
            model=self.model_info["id"],
            token=self.hf_token
        )
    
    def _init_openai_client(self):
        """Initialize OpenAI client."""
        self.client = OpenAI(api_key=self.openai_key)
    
    def _get_extraction_prompt(self) -> str:
        """Get the prompt for text extraction."""
        return """You are an expert document analyzer. Extract ALL text from this handwritten image.

Instructions:
1. Extract all visible handwritten text in reading order (left-to-right, top-to-bottom)
2. Preserve headings by using ## for main headings and ### for subheadings
3. Use **bold** for emphasized or underlined text
4. Use - for bullet points and 1. 2. 3. for numbered lists
5. For any diagrams or charts, describe them as [DIAGRAM: description]
6. For mathematical formulas, use $formula$ notation
7. For tables, use markdown table format

Extract all the text now:"""

    def extract_text(self, image: Image.Image) -> str:
        """
        Extract text from an image using the vision model.
        
        Args:
            image: PIL Image object
            
        Returns:
            Extracted text with formatting markers
        """
        if self.inference_type == "huggingface":
            return self._extract_via_huggingface(image)
        elif self.inference_type == "openai":
            return self._extract_via_openai(image)
        else:
            raise RuntimeError(f"Unknown inference type: {self.inference_type}")
    
    def _extract_via_huggingface(self, image: Image.Image) -> str:
        """Extract text using HuggingFace Inference API."""
        # Convert image to base64
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        prompt = self._get_extraction_prompt()
        
        try:
            # Use chat completion with image
            response = self.client.chat_completion(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_base64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                max_tokens=4096
            )
            return response.choices[0].message.content
        except Exception as e:
            # If the primary model fails, try alternative approach
            try:
                # Try image-to-text as fallback
                buffered.seek(0)
                result = self.client.image_to_text(buffered.getvalue())
                if isinstance(result, str):
                    return result
                elif hasattr(result, 'generated_text'):
                    return result.generated_text
                else:
                    return str(result)
            except Exception as e2:
                raise RuntimeError(f"HuggingFace API extraction failed: {str(e)}. Fallback also failed: {str(e2)}")
    
    def _extract_via_openai(self, image: Image.Image) -> str:
        """Extract text using OpenAI GPT-4 Vision API."""
        # Convert image to base64
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        prompt = self._get_extraction_prompt()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_info["id"],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_base64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                max_tokens=4096
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI GPT-4 Vision extraction failed: {str(e)}")


def parse_formatting_markers(text: str) -> dict:
    """
    Parse extracted text and identify formatting elements.
    
    Returns dict with:
        - headings: list of (level, text) tuples
        - bold_text: list of bold text segments
        - bullet_points: list of bullet point items
        - numbered_lists: list of numbered list items
        - diagrams: list of diagram descriptions
        - tables: list of table strings
        - paragraphs: list of regular paragraphs
    """
    result = {
        'headings': [],
        'bold_text': [],
        'bullet_points': [],
        'numbered_lists': [],
        'diagrams': [],
        'tables': [],
        'paragraphs': [],
        'formulas': []
    }
    
    lines = text.split('\n')
    current_table = []
    in_table = False
    
    for line in lines:
        stripped = line.strip()
        
        # Heading detection
        if stripped.startswith('## ') and not stripped.startswith('### '):
            result['headings'].append((2, stripped[3:]))
        elif stripped.startswith('### '):
            result['headings'].append((3, stripped[4:]))
        elif stripped.startswith('# '):
            result['headings'].append((1, stripped[2:]))
        # Bullet points
        elif stripped.startswith('- ') or stripped.startswith('* '):
            result['bullet_points'].append(stripped[2:])
        # Numbered lists
        elif re.match(r'^\d+\.\s', stripped):
            result['numbered_lists'].append(re.sub(r'^\d+\.\s', '', stripped))
        # Diagram markers
        elif '[DIAGRAM:' in stripped:
            diagram_match = re.search(r'\[DIAGRAM:\s*(.*?)\]', stripped)
            if diagram_match:
                result['diagrams'].append(diagram_match.group(1))
        # Table detection
        elif '|' in stripped and stripped.count('|') >= 2:
            in_table = True
            current_table.append(stripped)
        elif in_table and stripped:
            if '|' in stripped:
                current_table.append(stripped)
            else:
                result['tables'].append('\n'.join(current_table))
                current_table = []
                in_table = False
        # Regular paragraphs
        elif stripped and not any([
            stripped.startswith('#'),
            stripped.startswith('-'),
            stripped.startswith('*'),
            re.match(r'^\d+\.', stripped),
            '[DIAGRAM:' in stripped
        ]):
            result['paragraphs'].append(stripped)
        
        # Always check for inline formatting (bold, formulas) regardless of line type
        bold_matches = re.findall(r'\*\*(.*?)\*\*', stripped)
        result['bold_text'].extend(bold_matches)
        formula_matches = re.findall(r'\$(.*?)\$', stripped)
        result['formulas'].extend(formula_matches)
    
    # Handle any remaining table
    if current_table:
        result['tables'].append('\n'.join(current_table))
    
    return result
