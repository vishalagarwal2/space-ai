import json
import openai
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class LayoutGeneratorService:
    """
    Service for generating JSON layouts for social media posts based on brand guidelines
    """
    
    def __init__(self, business_profile):
        self.business_profile = business_profile
        
    def generate_layout(self, user_input: str, include_debug: bool = False, post_format: str = 'single') -> Dict[str, Any]:
        """
        Generate a JSON layout for a social media post
        
        Args:
            user_input: The user's request for the post
            include_debug: Whether to include debug information in the response
            
        Returns:
            Dictionary containing the layout JSON and optionally debug info
        """
        debug_info = {
            'user_input': user_input,
            'brand_context': '',
            'llm_prompt': '',
            'raw_llm_response': '',
            'parsing_errors': [],
            'used_fallback': False,
            'processing_steps': []
        }
        
        try:
            debug_info['processing_steps'].append('Building brand context')
            # Build brand context
            brand_context = self._build_brand_context()
            debug_info['brand_context'] = brand_context
            
            debug_info['processing_steps'].append('Generating layout with AI')
            # Generate layout using AI
            if post_format == 'carousel':
                layout_json, llm_debug = self._generate_carousel_layouts_with_ai(user_input, brand_context, include_debug=True)
            else:
                layout_json, llm_debug = self._generate_layout_with_ai(user_input, brand_context, include_debug=True)
            debug_info.update(llm_debug)
            
            debug_info['processing_steps'].append('Validating layout')
            # Validate and clean the layout
            validated_layout = self._validate_layout(layout_json)
            
            debug_info['processing_steps'].append('Layout generation completed successfully')
            
            if include_debug:
                validated_layout['_debug'] = debug_info
            
            return validated_layout
            
        except Exception as e:
            debug_info['processing_steps'].append(f'Error occurred: {str(e)}')
            debug_info['parsing_errors'].append(str(e))
            debug_info['used_fallback'] = True
            
            logger.error(f"[Layout Generator] Error generating layout: {str(e)}")
            logger.error(f"[Layout Generator] Exception type: {type(e).__name__}")
            if hasattr(e, '__traceback__'):
                import traceback
                logger.error(f"[Layout Generator] Traceback: {traceback.format_exc()}")
                debug_info['parsing_errors'].append(traceback.format_exc())
            
            # Return fallback layout
            logger.warning(f"[Layout Generator] Falling back to default layout for user input: {user_input[:100]}...")
            fallback_layout = self._get_fallback_layout(user_input)
            
            if include_debug:
                fallback_layout['_debug'] = debug_info
                
            return fallback_layout
    
    def _generate_carousel_layouts_with_ai(self, user_input: str, brand_context: str, include_debug: bool = False) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Generate carousel layouts (1-5 slides) using OpenAI
        
        Returns:
            Tuple of (carousel_data, debug_info)
        """
        
        system_prompt = f"""
You are an expert social media carousel designer. Generate JSON layout plans for Instagram carousel posts (1080x1080px per slide) based on user requests and brand guidelines.

CRITICAL CAROUSEL STRUCTURE - Follow This Pattern:
Carousels MUST have a clear narrative flow with:
1. INTRO SLIDE: Hook/attention-grabbing title that sets up the topic
2. CONTENT SLIDES (2-4 slides): Each focusing on ONE key point, numbered or themed
3. OUTRO SLIDE (optional but recommended): Summary, call-to-action, or contact info

EXAMPLE - Tailwind Financial "3 Financial Red Flags" Carousel:
This is a reference example showing proper carousel structure and continuity:

Slide 1 (INTRO): 
- Main headline: "3 FINANCIAL RED FLAGS"
- Subtitle: "You Might Be Ignoring"
- Purpose: Hook the viewer, create curiosity
- Design: Bold typography, brand colors, company logo

Slide 2 (CONTENT):
- Header: "Red Flag #1"
- Main content: "You have no Emergency Fund."
- Supporting text: "You're one small crisis away from serious debt."
- Design: Consistent branding, clear hierarchy

Slide 3 (CONTENT):
- Header: "Red Flag #2"  
- Main content: "You're juggling multiple 'Buy Now, Pay Later' (BNPL) loans"
- Supporting text: "It's a fast track to a debt trap"
- Design: Same visual style as Slide 2

Slide 4 (CONTENT):
- Header: "Red Flag #3"
- Main content: "You 'save', but you don't 'invest'."
- Supporting text: "Saving is for safety; investing is for growth."
- Design: Maintains consistency

Slide 5 (OUTRO):
- Summary or call-to-action
- Company branding/contact info
- Next steps for the viewer

KEY PRINCIPLES FROM THIS EXAMPLE:
1. Clear numbering/progression (Red Flag #1, #2, #3)
2. Consistent visual design across all slides
3. Each slide has ONE main message
4. Text is concise and impactful
5. Brand colors and logo present throughout
6. Logical flow from intro → content → conclusion

IMPORTANT: Create 3-5 slides for a carousel post. Each slide should focus on one key point or concept. The content should flow logically from slide to slide.

Your output must be valid JSON following this exact schema:

{{
  "post_type": "carousel",
  "slide_count": number (2-5),
  "slides": [
    {{
      "slide_number": number (1, 2, 3, etc.),
      "metadata": {{
        "dimensions": {{ "width": 1080, "height": 1080 }},
        "brand": {{
          "primary_color": string,
          "secondary_color": string,
          "font_family": string,
          "company_name": string
        }}
      }},
      "background": {{
        "type": "solid|linear-gradient|radial-gradient",
        "colors": [array of hex colors],
        "direction": number (for gradients, 0-360 degrees)
      }},
      "textBlocks": [
        {{
          "id": string,
          "text": string,
          "fontWeight": "normal|bold|600|700|800",
          "color": string (hex),
          "alignment": "left|center|right",
          "order": number (1-10, for sequential positioning),
          "maxWidth": number,
          "componentType": "headerText|bodyText|specialBannerText" (optional)
        }}
      ],
      "images": [
        {{
          "id": string,
          "src": "logo.png|icon.png",
          "width": number,
          "height": number,
          "position": {{ "x": number, "y": number }},
          "opacity": number (0-1)
        }}
      ],
      "shapes": [
        {{
          "id": string,
          "type": "circle|rectangle|line",
          "radius": number (for circles),
          "width": number (for rectangles/lines),
          "height": number (for rectangles),
          "color": string (hex),
          "opacity": number (0-1),
          "position": {{ "x": number, "y": number }}
        }}
      ]
    }}
  ]
}}

{brand_context}

Carousel Design Principles:
1. NARRATIVE STRUCTURE: Create 3-5 slides that tell a complete story with clear beginning, middle, and end
2. INTRO SLIDE (Slide 1): 
   - Create a hook/attention-grabbing headline
   - Use componentType "headerText" for the main title
   - Include a subtitle if needed using "bodyText"
   - Set up what the carousel will cover (e.g., "3 Financial Red Flags", "5 Steps to Success")
3. CONTENT SLIDES (Slides 2-4):
   - Each slide focuses on ONE main concept
   - Use clear numbering or progression indicators (e.g., "Red Flag #1", "Step 2", "Tip #3")
   - Header with the number/theme using "headerText" or "specialBannerText"
   - Main content point using "bodyText" 
   - Supporting detail or explanation using "bodyText" with lighter styling
4. OUTRO SLIDE (Final slide, optional):
   - Summary of key takeaways
   - Call-to-action (e.g., "Start Planning Today", "Contact Us")
   - Company branding/contact information
5. CONSISTENCY: Use the same visual style, colors, and layout structure across all slides
6. BRANDING: Position logo consistently (top-right corner) on every slide
7. TEXT HIERARCHY: Use componentType strategically:
   - "headerText" for main headlines and numbered items
   - "specialBannerText" for important callouts, numbers, or CTAs
   - "bodyText" for supporting information
8. READABILITY: Ensure high contrast, keep text concise (1-3 text blocks per slide max)
9. FLOW: Content should naturally progress from one slide to the next
10. EDUCATIONAL CONTENT: For educational carousels, break down complex topics into digestible, numbered points

TEXT POSITIONING GUIDELINES (SEQUENTIAL POSITIONING SYSTEM):
- Use "alignment" for horizontal placement: "left", "center", or "right"
- Use "order" to sequence text blocks from top to bottom (1 = first, 2 = second, 3 = third, etc.)
- Canvas will automatically calculate coordinates, handle font sizes, and prevent overlap with logo
- Focus on content hierarchy and sequential order instead of exact positioning

User Request: {user_input}

Generate a JSON carousel layout that creates an engaging, educational, brand-consistent Instagram carousel post.

{self._get_carousel_business_specific_examples()}

CRITICAL INSTRUCTIONS:
{self._get_design_component_instructions()}
5. Use brand colors consistently throughout all slides
6. Include illustration placeholders for products/services mentioned
7. Use sequential positioning with "alignment" and "order" only - DO NOT specify fontSize, areas, or pixel coordinates
8. Use white (#FFFFFF) text color for dark/colored backgrounds to ensure readability
9. Use maxWidth of 900px or less to prevent text from being cut off
10. NEVER create text blocks for hashtags - hashtags are handled separately
11. Each slide should have 1-3 text blocks maximum for clarity
12. Create logical flow between slides

Output only valid JSON, no additional text.
"""

        debug_info = {
            'llm_prompt': system_prompt,
            'user_message': f"Generate a carousel layout for: {user_input}",
            'raw_llm_response': '',
            'cleaned_response': '',
            'extracted_json': '',
            'parsing_errors': []
        }

        try:
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Using cheaper model for layout generation
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": debug_info['user_message']}
                ],
                max_tokens=2000,  # More tokens for carousel content
                temperature=0.3,  # Lower temperature for more consistent JSON structure
            )
            
            layout_content = response.choices[0].message.content.strip()
            debug_info['raw_llm_response'] = layout_content
            
            # Try to extract JSON from response (in case there's extra text)
            try:
                # Remove markdown code blocks if present
                cleaned_content = layout_content
                if cleaned_content.startswith('```json'):
                    cleaned_content = cleaned_content[7:]
                elif cleaned_content.startswith('```'):
                    cleaned_content = cleaned_content[3:]
                if cleaned_content.endswith('```'):
                    cleaned_content = cleaned_content[:-3]
                cleaned_content = cleaned_content.strip()
                
                debug_info['cleaned_response'] = cleaned_content
                
                # Find JSON content between first { and last }
                start_idx = cleaned_content.find('{')
                end_idx = cleaned_content.rfind('}') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_content = cleaned_content[start_idx:end_idx]
                    debug_info['extracted_json'] = json_content
                    
                    parsed_json = json.loads(json_content)
                    
                    return parsed_json, debug_info
                else:
                    raise ValueError("No JSON found in response")
                    
            except (json.JSONDecodeError, ValueError) as e:
                debug_info['parsing_errors'].append(str(e))
                logger.error(f"[Carousel Generator] Failed to parse AI-generated JSON: {e}")
                logger.error(f"[Carousel Generator] Raw response: {layout_content}")
                logger.error(f"[Carousel Generator] Cleaned content: {cleaned_content[:500]}")
                raise ValueError(f"Invalid JSON from AI: {e}")
                
        except Exception as e:
            debug_info['parsing_errors'].append(f"OpenAI API Error: {str(e)}")
            logger.error(f"[Carousel Generator] OpenAI API Error: {e}")
            raise
    
    def _get_carousel_business_specific_examples(self) -> str:
        """Get business-specific carousel examples based on company"""
        company_name = self.business_profile.company_name.lower()
        
        if 'tailwind' in company_name and 'financial' in company_name:
            return """
BUSINESS-SPECIFIC CONTEXT - Tailwind Financial Services:
You are creating content for Tailwind Financial Services, a professional financial services company.

REFERENCE CAROUSEL EXAMPLE - "3 Financial Red Flags You Might Be Ignoring":
This carousel demonstrates the EXACT structure and style to follow:

Slide 1 (INTRO):
{{
  "textBlocks": [
    {{"text": "3 FINANCIAL RED FLAGS", "componentType": "headerText", "fontWeight": "bold", "alignment": "center", "order": 1}},
    {{"text": "You Might Be Ignoring", "componentType": "bodyText", "alignment": "center", "order": 2}}
  ]
}}

Slide 2 (CONTENT):
{{
  "textBlocks": [
    {{"text": "Red Flag", "componentType": "bodyText", "alignment": "center", "order": 1}},
    {{"text": "#1", "componentType": "headerText", "fontWeight": "bold", "alignment": "center", "order": 2}},
    {{"text": "You have", "componentType": "bodyText", "alignment": "center", "order": 3}},
    {{"text": "no Emergency Fund.", "componentType": "specialBannerText", "fontWeight": "bold", "alignment": "center", "order": 4}},
    {{"text": "You're one small crisis away from serious debt.", "componentType": "bodyText", "alignment": "center", "order": 5}}
  ]
}}

Slide 3 (CONTENT):
{{
  "textBlocks": [
    {{"text": "Red Flag", "componentType": "bodyText", "alignment": "center", "order": 1}},
    {{"text": "#2", "componentType": "headerText", "fontWeight": "bold", "alignment": "center", "order": 2}},
    {{"text": "You're juggling multiple", "componentType": "bodyText", "alignment": "center", "order": 3}},
    {{"text": "\\"Buy Now, Pay Later\\"", "componentType": "specialBannerText", "fontWeight": "bold", "alignment": "center", "order": 4}},
    {{"text": "(BNPL) loans", "componentType": "bodyText", "alignment": "center", "order": 5}},
    {{"text": "It's a fast track to a debt trap", "componentType": "bodyText", "alignment": "center", "order": 6}}
  ]
}}

Slide 4 (CONTENT):
{{
  "textBlocks": [
    {{"text": "Red Flag", "componentType": "bodyText", "alignment": "center", "order": 1}},
    {{"text": "#3", "componentType": "headerText", "fontWeight": "bold", "alignment": "center", "order": 2}},
    {{"text": "You \\"save\\", but", "componentType": "bodyText", "alignment": "center", "order": 3}},
    {{"text": "you don't \\"invest\\".", "componentType": "specialBannerText", "fontWeight": "bold", "alignment": "center", "order": 4}},
    {{"text": "Saving is for safety; investing is for growth.", "componentType": "bodyText", "alignment": "center", "order": 5}}
  ]
}}

KEY TAKEAWAYS FOR TAILWIND FINANCIAL CAROUSELS:
1. Use UPPERCASE for main headlines (componentType: "headerText")
2. Use "specialBannerText" for key financial terms and important concepts
3. Break content into clear, numbered points (#1, #2, #3)
4. Keep text concise and impactful
5. Use center alignment for professional, balanced look
6. Each slide has 4-6 text blocks maximum
7. Maintain consistent structure across all content slides
8. Use the brand's professional blue color palette
9. Educational tone focused on financial literacy
10. Create curiosity and provide actionable insights
"""
        else:
            return ""
    
    def _build_brand_context(self) -> str:
        """Build brand context string from business profile"""
        return f"""
Brand Guidelines:
- Company: {self.business_profile.company_name}
- Industry: {self.business_profile.industry}
- Primary Color: {self.business_profile.primary_color}
- Secondary Color: {self.business_profile.secondary_color}
- Font Family: {self.business_profile.font_family}
- Brand Voice: {self.business_profile.brand_voice}
- Target Audience: {self.business_profile.target_audience}
- Business Description: {self.business_profile.business_description}
"""
    
    def _get_design_component_instructions(self) -> str:
        """Generate design component instructions based on business profile"""
        # Check if business profile has design components
        if hasattr(self.business_profile, 'design_components') and self.business_profile.design_components:
            design_components = self.business_profile.design_components
            
            # Build instructions from business profile design components
            instructions = f"""
1. COMPANY-SPECIFIC DESIGN COMPONENTS - {design_components.get('instructions', 'Use company-specific design language')}

   COMPONENT TYPE USAGE - Use componentType to create visual hierarchy:
"""
            
            component_rules = design_components.get('componentRules', {})
            
            # Header Text Component
            if 'headerText' in component_rules:
                header_rule = component_rules['headerText']
                styling = header_rule.get('styling', {})
                instructions += f"""
   A) "headerText" - {header_rule.get('description', 'For main headlines')}
      - {header_rule.get('usage', 'Use for main headlines')}
      - Styling: {styling.get('additionalStyles', 'Large font size, bold styling')}
      - Text Transform: {styling.get('textTransform', 'none')}
      - Color: {"Primary brand color" if styling.get('color') == 'primary' else styling.get('color', '#333333')}
      - Font Weight: {styling.get('fontWeight', 'bold')}
      - Example: {{"text": "SAMPLE HEADLINE", "componentType": "headerText", "fontWeight": "{styling.get('fontWeight', 'bold')}", "alignment": "center", "order": 1}}
"""
            
            # Body Text Component
            if 'bodyText' in component_rules:
                body_rule = component_rules['bodyText']
                styling = body_rule.get('styling', {})
                instructions += f"""
   B) "bodyText" - {body_rule.get('description', 'For supporting content')}
      - {body_rule.get('usage', 'Use for supporting information')}
      - Styling: {styling.get('additionalStyles', 'Medium font size, standard styling')}
      - Text Transform: {styling.get('textTransform', 'none')}
      - Color: {styling.get('color', '#333333')}
      - Font Weight: {styling.get('fontWeight', 'normal')}
      - Example: {{"text": "Supporting information text", "componentType": "bodyText", "alignment": "center", "order": 2}}
"""
            
            # Special Banner Text Component
            if 'specialBannerText' in component_rules:
                banner_rule = component_rules['specialBannerText']
                styling = banner_rule.get('styling', {})
                instructions += f"""
   C) "specialBannerText" - {banner_rule.get('description', 'For highlighted offers/CTAs')}
      - {banner_rule.get('usage', 'Use for special offers and CTAs')}
      - Styling: {styling.get('additionalStyles', 'Prominent styling with background banner')}
      - Text Transform: {styling.get('textTransform', 'none')}
      - Color: {styling.get('color', '#FFFFFF')}
      - Background: {"Primary brand color" if styling.get('backgroundColor') == 'primary' else styling.get('backgroundColor', 'primary color')}
      - Font Weight: {styling.get('fontWeight', 'bold')}
      - Example: {{"text": "SPECIAL OFFER", "componentType": "specialBannerText", "alignment": "center", "order": 3}}
"""
            
            instructions += """
2. MAIN SLOGAN RECOGNITION: If user mentions text in quotes, use "headerText" componentType
3. OFFERS & NUMBERS: Money amounts, percentages, special deals should use "specialBannerText"
4. SUPPORTING INFO: Everything else uses "bodyText" componentType"""
            
            return instructions
        
        # Fallback to default instructions if no design components found
        return """
1. COMPONENT TYPE USAGE - Use componentType to create visual hierarchy:

   A) "headerText" - For main slogans/headlines (like "Scrap. Save. Smile.")
      - Gets LARGE font size, bold styling, maximum visual impact
      - Use when: Main slogan, primary headline, key catchphrase
      - Example: {{"text": "Scrap. Save. Smile.", "componentType": "headerText", "fontWeight": "bold", "alignment": "center", "order": 1}}

   B) "bodyText" - For regular supporting content
      - Gets medium font size, standard styling
      - Use when: Supporting information, descriptions, secondary messages
      - Example: {{"text": "Your old ride just earned you a sweet reward!", "componentType": "bodyText", "alignment": "center", "order": 2}}

   C) "specialBannerText" - For highlighted offers/CTAs (like "Upto ₹75,000 Road Tax Rebate")
      - Gets prominent styling with background color banner/pill effect
      - Use when: Special offers, important numbers, call-to-action buttons
      - Example: {{"text": "Upto ₹75,000 Road Tax Rebate", "componentType": "specialBannerText", "alignment": "center", "order": 3}}

2. MAIN SLOGAN RECOGNITION: If user mentions text in quotes, use "headerText" componentType
3. OFFERS & NUMBERS: Money amounts, percentages, special deals should use "specialBannerText"
4. SUPPORTING INFO: Everything else uses "bodyText" componentType"""
    
    def _generate_layout_with_ai(self, user_input: str, brand_context: str, include_debug: bool = False) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Generate layout JSON using OpenAI
        
        Returns:
            Tuple of (layout_json, debug_info)
        """
        
        system_prompt = f"""
You are an expert social media layout designer. Generate JSON layout plans for Instagram posts (1080x1080px) based on user requests and brand guidelines.

IMPORTANT: Pay special attention to extracting custom text, numbers, offers, and specific details from the user's request. These should be prominently featured in the layout. Look for:
- Specific offers (e.g., "Up to ₹75,000 rebate", "25% off", etc.)
- Custom messaging and slogans
- Company-specific text and taglines
- Product or service names
- Contact information or calls-to-action

Your output must be valid JSON following this exact schema:

{{
  "metadata": {{
    "dimensions": {{ "width": 1080, "height": 1080 }},
    "brand": {{
      "primary_color": string,
      "secondary_color": string,
      "font_family": string,
      "company_name": string
    }}
  }},
  "background": {{
    "type": "solid|linear-gradient|radial-gradient",
    "colors": [array of hex colors],
    "direction": number (for gradients, 0-360 degrees)
  }},
  "textBlocks": [
    {{
      "id": string,
      "text": string,
      "fontWeight": "normal|bold|600|700|800",
      "color": string (hex),
      "alignment": "left|center|right",
      "order": number (1-10, for sequential positioning),
      "maxWidth": number,
      "componentType": "headerText|bodyText|specialBannerText" (optional)
    }}
  ],
  "images": [
    {{
      "id": string,
      "src": "logo.png|icon.png",
      "width": number,
      "height": number,
      "position": {{ "x": number, "y": number }},
      "opacity": number (0-1)
    }}
  ],
  "shapes": [
    {{
      "id": string,
      "type": "circle|rectangle|line",
      "radius": number (for circles),
      "width": number (for rectangles/lines),
      "height": number (for rectangles),
      "color": string (hex),
      "opacity": number (0-1),
      "position": {{ "x": number, "y": number }}
    }}
  ]
}}

{brand_context}

Design Principles:
1. Use brand colors prominently
2. Ensure text is readable (high contrast)
3. Position logo in top-right corner (920-980px from left, 40-80px from top)
4. Maintain visual hierarchy with font sizes
5. Leave adequate white space
6. Keep text concise and impactful
7. Use consistent spacing (multiples of 20px)
8. Extract and highlight any custom text, numbers, or offers mentioned by the user
9. Create clear sections for branding, main message, and call-to-action as appropriate
10. Use illustration placeholders for product/service visuals

TEXT POSITIONING GUIDELINES (SEQUENTIAL POSITIONING SYSTEM):
- Use "alignment" for horizontal placement: "left", "center", or "right"
- Use "order" to sequence text blocks from top to bottom (1 = first, 2 = second, 3 = third, etc.)
- Canvas will automatically calculate coordinates, handle font sizes, and prevent overlap with logo
- Example: Main headline = {{"alignment": "center", "order": 1}}
- Example: Subtitle = {{"alignment": "center", "order": 2}}
- Example: Body text = {{"alignment": "left", "order": 3}}
- Example: CTA button = {{"alignment": "center", "order": 4}}
- DO NOT specify fontSize, areas, or pixel coordinates - the canvas renderer handles all positioning and sizing
- Focus on content hierarchy and sequential order instead of exact positioning

User Request: {user_input}

Generate a JSON layout that creates an engaging, brand-consistent Instagram post. 

CRITICAL INSTRUCTIONS:
{self._get_design_component_instructions()}
5. Use brand colors consistently throughout the layout
6. Include illustration placeholders for products/services mentioned
7. Use sequential positioning with "alignment" and "order" only - DO NOT specify fontSize, areas, or pixel coordinates
8. Use white (#FFFFFF) text color for dark/colored backgrounds to ensure readability
9. Use maxWidth of 900px or less to prevent text from being cut off
10. NEVER create text blocks for hashtags - hashtags are handled separately and should NOT appear in textBlocks array
11. Canvas renderer will handle all font sizing, positioning, and logo collision detection automatically
12. Focus on 1 main message + max 2-3 supporting elements for clean, impactful design

Output only valid JSON, no additional text.
"""

        debug_info = {
            'llm_prompt': system_prompt,
            'user_message': f"Generate a JSON layout for: {user_input}",
            'raw_llm_response': '',
            'cleaned_response': '',
            'extracted_json': '',
            'parsing_errors': []
        }

        try:
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Using cheaper model for layout generation
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": debug_info['user_message']}
                ],
                max_tokens=1000,
                temperature=0.3,  # Lower temperature for more consistent JSON structure
            )
            
            layout_content = response.choices[0].message.content.strip()
            debug_info['raw_llm_response'] = layout_content
            
            
            # Try to extract JSON from response (in case there's extra text)
            try:
                # Remove markdown code blocks if present
                cleaned_content = layout_content
                if cleaned_content.startswith('```json'):
                    cleaned_content = cleaned_content[7:]
                elif cleaned_content.startswith('```'):
                    cleaned_content = cleaned_content[3:]
                if cleaned_content.endswith('```'):
                    cleaned_content = cleaned_content[:-3]
                cleaned_content = cleaned_content.strip()
                
                debug_info['cleaned_response'] = cleaned_content
                
                # Find JSON content between first { and last }
                start_idx = cleaned_content.find('{')
                end_idx = cleaned_content.rfind('}') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_content = cleaned_content[start_idx:end_idx]
                    debug_info['extracted_json'] = json_content
                    
                    parsed_json = json.loads(json_content)
                    
                    return parsed_json, debug_info
                else:
                    raise ValueError("No JSON found in response")
                    
            except (json.JSONDecodeError, ValueError) as e:
                debug_info['parsing_errors'].append(str(e))
                logger.error(f"[Layout Generator] Failed to parse AI-generated JSON: {e}")
                logger.error(f"[Layout Generator] Raw response: {layout_content}")
                logger.error(f"[Layout Generator] Cleaned content: {cleaned_content[:500]}")
                raise ValueError(f"Invalid JSON from AI: {e}")
                
        except Exception as e:
            debug_info['parsing_errors'].append(f"OpenAI API Error: {str(e)}")
            logger.error(f"[Layout Generator] OpenAI API Error: {e}")
            raise
    
    def _validate_layout(self, layout: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and ensure required fields are present"""
        
        # Ensure required top-level keys
        required_keys = ['metadata', 'background', 'textBlocks', 'images', 'shapes']
        for key in required_keys:
            if key not in layout:
                layout[key] = []
                
        # Validate metadata
        if 'metadata' not in layout or not isinstance(layout['metadata'], dict):
            layout['metadata'] = {
                'dimensions': {'width': 1080, 'height': 1080},
                'brand': {
                    'primary_color': self.business_profile.primary_color,
                    'secondary_color': self.business_profile.secondary_color,
                    'font_family': self.business_profile.font_family,
                    'company_name': self.business_profile.company_name
                }
            }
        else:
            # Ensure brand object exists and has correct font_family from business profile
            if 'brand' not in layout['metadata'] or not isinstance(layout['metadata']['brand'], dict):
                layout['metadata']['brand'] = {}
            
            # Always use the font_family from business profile (don't trust AI-generated font)
            layout['metadata']['brand']['font_family'] = self.business_profile.font_family
            # Also ensure other brand fields are set correctly
            if 'primary_color' not in layout['metadata']['brand']:
                layout['metadata']['brand']['primary_color'] = self.business_profile.primary_color
            if 'secondary_color' not in layout['metadata']['brand']:
                layout['metadata']['brand']['secondary_color'] = self.business_profile.secondary_color
            if 'company_name' not in layout['metadata']['brand']:
                layout['metadata']['brand']['company_name'] = self.business_profile.company_name
            
        # Validate background
        if 'background' not in layout or not isinstance(layout['background'], dict):
            layout['background'] = {
                'type': 'linear-gradient',
                'colors': [self.business_profile.primary_color, self.business_profile.secondary_color],
                'direction': 45
            }
            
        # Ensure arrays are actually arrays
        for array_key in ['textBlocks', 'images', 'shapes']:
            if not isinstance(layout.get(array_key), list):
                layout[array_key] = []
        
        # Remove any hashtag text blocks (defensive filtering)
        original_text_blocks = len(layout.get('textBlocks', []))
        layout['textBlocks'] = [
            block for block in layout.get('textBlocks', []) 
            if not (
                isinstance(block, dict) and 
                (
                    block.get('id', '').lower() in ['hashtags', 'hashtag'] or 
                    '#' in str(block.get('text', ''))[:10]  # Check first 10 chars for hashtags
                )
            )
        ]
        filtered_text_blocks = len(layout['textBlocks'])
        if original_text_blocks != filtered_text_blocks:
            logger.info(f"🚫 [Layout Validation] Removed {original_text_blocks - filtered_text_blocks} hashtag text blocks")
                
        # Add logo if not present
        has_logo = any(img.get('src', '').startswith('logo') for img in layout['images'])
        if not has_logo and self.business_profile.logo_url:
            layout['images'].append({
                'id': 'brand-logo',
                'src': 'logo.png',
                'width': 100,
                'height': 100,
                'position': {'x': 920, 'y': 60},
                'opacity': 1.0
            })
                
        return layout
    
    def _get_fallback_layout(self, user_input: str) -> Dict[str, Any]:
        """Return a basic fallback layout if AI generation fails"""
        
        # Generate a simple, safe message instead of using raw user input
        safe_headline = f"New Post from {self.business_profile.company_name}"
        safe_subtitle = "We're excited to share this with you!"
        
        logger.warning(f"Using fallback layout for input: {user_input[:100]}...")
        
        return {
            "metadata": {
                "dimensions": {"width": 1080, "height": 1080},
                "brand": {
                    "primary_color": self.business_profile.primary_color,
                    "secondary_color": self.business_profile.secondary_color,
                    "font_family": self.business_profile.font_family,
                    "company_name": self.business_profile.company_name
                }
            },
            "background": {
                "type": "linear-gradient",
                "colors": [self.business_profile.primary_color, self.business_profile.secondary_color],
                "direction": 135
            },
            "textBlocks": [
                {
                    "id": "main-text",
                    "text": safe_headline,
                    "fontWeight": "bold",
                    "color": "#FFFFFF",
                    "alignment": "center",
                    "order": 1,
                    "maxWidth": 800
                },
                {
                    "id": "subtitle-text",
                    "text": safe_subtitle,
                    "fontWeight": "normal",
                    "color": "#FFFFFFCC",
                    "alignment": "center",
                    "order": 2,
                    "maxWidth": 700
                },
                {
                    "id": "company-name", 
                    "text": self.business_profile.company_name,
                    "fontWeight": "normal",
                    "color": "#FFFFFFCC",
                    "alignment": "center",
                    "order": 3,
                    "maxWidth": 600
                }
            ],
            "images": [
                {
                    "id": "logo",
                    "src": "logo.png", 
                    "width": 100,
                    "height": 100,
                    "position": {"x": 920, "y": 60},
                    "opacity": 1.0
                }
            ],
            "shapes": []
        }
    
    def generate_carousel_layouts(self, user_input: str, include_debug: bool = False, num_slides: int = 3) -> list[Dict[str, Any]]:
        """
        Generate multiple JSON layouts for a carousel post
        
        Args:
            user_input: The user's request for the post
            include_debug: Whether to include debug information in the response
            num_slides: Number of slides to generate (default 3)
            
        Returns:
            List of layout dictionaries for each carousel slide
        """
        try:
            # For educational content, break down the content into multiple slides
            carousel_layouts = []
            
            # Generate a comprehensive layout first to understand the content
            base_layout = self.generate_layout(user_input, include_debug=False)
            
            # Extract text blocks from the base layout
            text_blocks = base_layout.get('textBlocks', [])
            
            if len(text_blocks) <= 1:
                # If there's not enough content for a carousel, create slides with different focuses
                slides_content = self._generate_educational_slides(user_input, num_slides)
            else:
                # Split existing content across slides
                slides_content = self._split_content_into_slides(text_blocks, num_slides)
            
            # Generate a layout for each slide
            for i, slide_content in enumerate(slides_content):
                slide_layout = self._generate_slide_layout(slide_content, base_layout, i + 1, len(slides_content))
                if include_debug:
                    slide_layout['_debug'] = {
                        'slide_number': i + 1,
                        'total_slides': len(slides_content),
                        'content_focus': slide_content.get('focus', 'general')
                    }
                carousel_layouts.append(slide_layout)
            
            return carousel_layouts
            
        except Exception as e:
            logger.error(f"[Carousel Generator] Error generating carousel layouts: {str(e)}")
            # Fallback: create 3 variations of the single layout
            base_layout = self.generate_layout(user_input, include_debug=False)
            return [base_layout] * 3
    
    def _generate_educational_slides(self, user_input: str, num_slides: int) -> list[Dict[str, Any]]:
        """Generate educational content slides based on user input"""
        # This could be enhanced with AI to break down educational content
        # For now, create basic slide structure
        slides = []
        
        # Slide 1: Introduction/Problem
        slides.append({
            'focus': 'introduction',
            'title': 'Introduction',
            'content': f"Learn about {user_input}",
            'type': 'intro'
        })
        
        # Slide 2: Main Content/Solution
        slides.append({
            'focus': 'main_content',
            'title': 'Key Information',
            'content': f"Important details about {user_input}",
            'type': 'content'
        })
        
        # Slide 3: Call to Action/Summary
        slides.append({
            'focus': 'conclusion',
            'title': 'Take Action',
            'content': f"Ready to get started with {user_input}?",
            'type': 'cta'
        })
        
        return slides[:num_slides]
    
    def _split_content_into_slides(self, text_blocks: list, num_slides: int) -> list[Dict[str, Any]]:
        """Split existing text blocks into carousel slides"""
        slides = []
        blocks_per_slide = max(1, len(text_blocks) // num_slides)
        
        for i in range(num_slides):
            start_idx = i * blocks_per_slide
            end_idx = start_idx + blocks_per_slide if i < num_slides - 1 else len(text_blocks)
            
            slide_blocks = text_blocks[start_idx:end_idx]
            slides.append({
                'focus': f'slide_{i+1}',
                'text_blocks': slide_blocks,
                'type': 'content'
            })
        
        return slides
    
    def _generate_slide_layout(self, slide_content: Dict[str, Any], base_layout: Dict[str, Any], slide_num: int, total_slides: int) -> Dict[str, Any]:
        """Generate layout for a specific carousel slide"""
        # Start with base layout structure
        slide_layout = {
            'metadata': base_layout['metadata'].copy(),
            'background': base_layout['background'].copy(),
            'images': base_layout['images'].copy(),
            'shapes': base_layout['shapes'].copy(),
            'textBlocks': []
        }
        
        # Add slide indicator
        slide_layout['textBlocks'].append({
            'id': 'slide_indicator',
            'text': f'{slide_num}/{total_slides}',
            'fontWeight': 'normal',
            'color': '#666666',
            'alignment': 'right',
            'order': 0,
            'maxWidth': 100,
            'componentType': 'bodyText'
        })
        
        # Add slide-specific content
        if 'text_blocks' in slide_content:
            # Use existing text blocks
            for block in slide_content['text_blocks']:
                slide_layout['textBlocks'].append(block)
        else:
            # Generate new text blocks based on slide focus
            if slide_content['type'] == 'intro':
                slide_layout['textBlocks'].extend([
                    {
                        'id': 'slide_title',
                        'text': slide_content['title'],
                        'fontWeight': 'bold',
                        'color': base_layout['metadata']['brand']['primary_color'],
                        'alignment': 'center',
                        'order': 1,
                        'maxWidth': 800,
                        'componentType': 'headerText'
                    },
                    {
                        'id': 'slide_content',
                        'text': slide_content['content'],
                        'fontWeight': 'normal',
                        'color': '#333333',
                        'alignment': 'center',
                        'order': 2,
                        'maxWidth': 700,
                        'componentType': 'bodyText'
                    }
                ])
            elif slide_content['type'] == 'cta':
                slide_layout['textBlocks'].extend([
                    {
                        'id': 'slide_title',
                        'text': slide_content['title'],
                        'fontWeight': 'bold',
                        'color': base_layout['metadata']['brand']['primary_color'],
                        'alignment': 'center',
                        'order': 1,
                        'maxWidth': 800,
                        'componentType': 'headerText'
                    },
                    {
                        'id': 'slide_content',
                        'text': slide_content['content'],
                        'fontWeight': '600',
                        'color': '#ffffff',
                        'alignment': 'center',
                        'order': 2,
                        'maxWidth': 600,
                        'componentType': 'specialBannerText'
                    }
                ])
            else:
                # Default content slide
                slide_layout['textBlocks'].extend([
                    {
                        'id': 'slide_title',
                        'text': slide_content['title'],
                        'fontWeight': 'bold',
                        'color': base_layout['metadata']['brand']['primary_color'],
                        'alignment': 'center',
                        'order': 1,
                        'maxWidth': 800,
                        'componentType': 'headerText'
                    },
                    {
                        'id': 'slide_content',
                        'text': slide_content['content'],
                        'fontWeight': 'normal',
                        'color': '#333333',
                        'alignment': 'left',
                        'order': 2,
                        'maxWidth': 700,
                        'componentType': 'bodyText'
                    }
                ])
        
        return slide_layout

