"""
Digital product generator for creating comprehensive products alongside blog posts
"""
import logging
import json
import re
import zipfile
from pathlib import Path
from typing import Dict, Optional, List
from openai import OpenAI
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DigitalProductGenerator:
    """Generates comprehensive digital products from blog content"""
    
    def __init__(self):
        self.client = OpenAI(api_key=config.openai_api_key)
        self.output_dir = config.output_dir / "digital_products"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_product(self, blog_title: str, blog_content: str, 
                       blog_tags: List[str], blog_niche: str, 
                       topic_demand: str = 'medium') -> Optional[Dict]:
        """Generate a packaged utility only when the topic supports a useful product."""
        logger.info(f"Generating digital product for: {blog_title} (demand: {topic_demand})")
        opportunity = self._assess_product_opportunity(blog_title, blog_content, blog_niche)
        if not opportunity:
            logger.info("No standalone utility opportunity for this topic; skipping Gumroad product")
            return None

        app_html = self._generate_browser_utility(blog_title, blog_content, opportunity)
        if not app_html:
            logger.warning("Could not create a valid packaged utility; skipping product")
            return None
        return {
            'title': opportunity['title'][:60],
            'description': opportunity['description'],
            'content': app_html,
            'utility_name': opportunity['utility_name'],
            'problem': opportunity['problem'],
            'pricing': self._suggest_pricing(blog_niche, topic_demand),
            'demand_level': topic_demand,
            'niche': blog_niche,
            'quality_score': 100,
            'checklist': [],
            'templates': [],
            'tools': [],
            'marketing_copy': opportunity['description'],
        }

    def _assess_product_opportunity(self, title: str, content: str, niche: str) -> Optional[Dict]:
        """Return a concrete utility brief or reject topics that only support editorial content."""
        try:
            response = self.client.chat.completions.create(
                model=config.openai_model_digital_product,
                max_tokens=500,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "Assess whether a blog topic supports a useful standalone interactive browser utility. Reject opinion, news, broad explainers, and topics where a free article is sufficient. Accept only a repeated, specific user task that a self-contained browser app can materially simplify. Return JSON: {\"fit\": boolean, \"utility_name\": string, \"problem\": string, \"title\": string, \"description\": string}. Be conservative."},
                    {"role": "user", "content": f"Niche: {niche}\nTopic: {title}\nArticle: {content[:2500]}\nOnly accept a tool with a clear input, useful output, and audience who would use it repeatedly."}
                ]
            )
            data = json.loads(response.choices[0].message.content)
            required = ('utility_name', 'problem', 'title', 'description')
            if not data.get('fit') or any(not str(data.get(k, '')).strip() for k in required):
                return None
            return data
        except Exception as exc:
            logger.warning(f"Product opportunity assessment failed: {exc}")
            return None

    def _generate_browser_utility(self, title: str, content: str, brief: Dict) -> Optional[str]:
        """Generate a self-contained HTML app; reject code snippets and script-only outputs."""
        try:
            response = self.client.chat.completions.create(
                model=config.openai_model_digital_product,
                max_tokens=config.max_tokens_digital_product,
                messages=[
                    {"role": "system", "content": "Build polished, genuinely useful single-file browser applications in plain HTML/CSS/JavaScript. Output only complete HTML, with no markdown fences. The app must work offline, have a clear form/input and actionable result, validate input, be responsive and accessible, and require no external services or dependencies. Do not output a tutorial, shell, or standalone script."},
                    {"role": "user", "content": f"Create a complete offline browser utility named {brief['utility_name']} for this problem: {brief['problem']}\nContext: {title}\n{content[:2000]}\nMake it useful on its own, not a demo. Include practical defaults and copy/export results where relevant."}
                ]
            )
            html = response.choices[0].message.content.strip()
            html = re.sub(r'^```(?:html)?\s*|\s*```$', '', html, flags=re.IGNORECASE)
            if '<html' not in html.lower() or '<script' not in html.lower() or len(html) < 1200:
                return None
            return html
        except Exception as exc:
            logger.warning(f"Browser utility generation failed: {exc}")
            return None
    
    def _validate_product_quality(self, product_data: Dict) -> int:
        """Validate product quality and return a score out of 100"""
        score = 0
        max_score = 100
        
        # Content length check (20 points)
        content_length = len(product_data.get('content', ''))
        if content_length > 4000:
            score += 20
        elif content_length > 3000:
            score += 15
        elif content_length > 2000:
            score += 10
        
        # Functional tools quality (30 points) - NEW PRIORITY
        tools = product_data.get('tools', [])
        if len(tools) >= 3:
            score += 30
        elif len(tools) >= 2:
            score += 20
        elif len(tools) >= 1:
            score += 10
        
        # Checklist quality (15 points)
        checklist = product_data.get('checklist', [])
        if len(checklist) >= 15:
            score += 15
        elif len(checklist) >= 10:
            score += 10
        elif len(checklist) >= 5:
            score += 5
        
        # Templates quality (20 points)
        templates = product_data.get('templates', [])
        if len(templates) >= 5:
            score += 20
        elif len(templates) >= 3:
            score += 15
        elif len(templates) >= 1:
            score += 5
        
        # Description quality (10 points)
        description = product_data.get('description', '')
        if len(description) > 200:
            score += 10
        elif len(description) > 100:
            score += 5
        
        # Marketing copy quality (5 points)
        marketing = product_data.get('marketing_copy', '')
        if len(marketing) > 150:
            score += 5
        elif len(marketing) > 100:
            score += 3
        
        return min(score, max_score)
    
    def _generate_minimal_product(self, blog_title: str, blog_content: str) -> Dict:
        """Generate a minimal product as fallback when full generation fails"""
        logger.warning("Generating minimal product as fallback")
        return {
            'title': f"Complete Guide: {blog_title}",
            'description': f"A comprehensive guide expanding on {blog_title}, including detailed implementation steps and practical examples.",
            'content': blog_content,  # Use blog content as fallback
            'checklist': [
                "Review the blog post for key concepts",
                "Implement the suggested approaches",
                "Test your implementation",
                "Iterate based on results"
            ],
            'templates': [],
            'pricing': 9.99,
            'marketing_copy': f"Get the complete guide to {blog_title} with this comprehensive digital product."
        }
    
    def _generate_product_title(self, blog_title: str) -> str:
        """Generate a compelling product title"""
        try:
            response = self.client.chat.completions.create(
                model=config.openai_model_digital_product,
                max_tokens=100,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at creating compelling digital product titles. Create titles that are actionable, specific, and promise clear value. Return ONLY the title, no explanations or options."
                    },
                    {
                        "role": "user",
                        "content": f"Create a single, compelling digital product title based on this blog post title: {blog_title}\n\nThe product should be a comprehensive guide, template pack, or checklist that expands on the blog topic. Make it sound premium and valuable.\n\nReturn ONLY the title, nothing else. Maximum 60 characters."
                    }
                ]
            )
            
            title = response.choices[0].message.content.strip()
            # Remove any quotes and limit length
            title = title.strip('"\'').strip()
            if len(title) > 60:
                title = title[:60].strip()
            return title
        except Exception as e:
            logger.error(f"Error generating product title: {e}")
            return f"Complete Guide: {blog_title}"
    
    def _generate_product_description(self, blog_title: str, blog_content: str) -> str:
        """Generate a compelling product description for Gumroad"""
        try:
            response = self.client.chat.completions.create(
                model=config.openai_model_digital_product,
                max_tokens=500,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert copywriter for digital products. Create compelling, benefit-focused descriptions that highlight value and outcomes."
                    },
                    {
                        "role": "user",
                        "content": f"Create a compelling Gumroad product description for a digital product based on:\n\nBlog Title: {blog_title}\nBlog Content: {blog_content[:500]}...\n\nThe product includes:\n- Comprehensive guide and documentation\n- Functional tools, scripts, and applications\n- Ready-to-use templates and code\n- Step-by-step implementation guides\n- Troubleshooting and optimization tips\n\nThe description should:\n- Hook the reader immediately\n- Highlight the functional tools and their value\n- Emphasize time savings and problem-solving capabilities\n- Mention these are NOT just tutorials but working tools\n- Create urgency and desire\n- Be 200-300 words"
                    }
                ]
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating product description: {e}")
            return f"A comprehensive digital product expanding on {blog_title}. Includes detailed guides, templates, and checklists."
    
    def _generate_comprehensive_content(self, blog_title: str, blog_content: str, blog_niche: str) -> str:
        """Generate comprehensive content for the digital product"""
        try:
            response = self.client.chat.completions.create(
                model=config.openai_model_digital_product,
                max_tokens=config.max_tokens_digital_product,
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are a world-class expert in {blog_niche} with deep practical experience. 
                        You create premium digital products that provide exceptional value and actionable insights.
                        
                        Your content standards:
                        - Go 10x deeper than typical blog content
                        - Include specific, actionable steps readers can implement immediately
                        - Provide real code examples, configurations, or templates
                        - Include troubleshooting guides and common pitfalls
                        - Add advanced tips and techniques not found in free content
                        - Structure content logically with clear progression
                        - Include metrics, benchmarks, or performance indicators
                        - Add case studies from real implementations
                        - Provide alternative approaches and when to use each
                        
                        Your goal: Create content that readers would happily pay $20-50 for because it saves them hours of research and implementation time."""
                    },
                    {
                        "role": "user",
                        "content": f"""Create premium, comprehensive content for a digital product based on:\n\nBlog Title: {blog_title}\nBlog Content: {blog_content}\n\nThe content should:\n- Be 4000-6000 words of premium content\n- Go much deeper than the blog post - this is the paid product\n- Include detailed step-by-step instructions with specific commands/settings\n- Provide 3-5 real code examples, configurations, or templates\n- Include troubleshooting section with common issues and solutions\n- Add advanced tips and techniques not commonly known\n- Include performance metrics, benchmarks, or success criteria\n- Add 2-3 real case studies or implementation examples\n- Include a quick start guide for immediate implementation\n- Add a resources section with tools, libraries, or references\n- Be structured with clear sections: Introduction, Quick Start, Deep Dive, Advanced Topics, Troubleshooting, Case Studies, Resources\n- Use professional markdown formatting with code blocks, tables, and callouts\n- Include specific file names, paths, commands, or configuration values\n- Add decision trees or flowcharts for complex processes\n- Include checklists or worksheets for implementation tracking"""
                    }
                ]
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating comprehensive content: {e}")
            return blog_content  # Fallback to blog content
    
    def _generate_checklist(self, blog_title: str, blog_content: str) -> List[str]:
        """Generate a comprehensive, actionable checklist based on the content"""
        try:
            response = self.client.chat.completions.create(
                model=config.openai_model_digital_product,
                max_tokens=1500,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at creating comprehensive, actionable implementation checklists. Create specific, measurable, and time-bound checklist items that readers can actually follow."
                    },
                    {
                        "role": "user",
                        "content": f"Create a comprehensive implementation checklist based on:\n\nBlog Title: {blog_title}\nBlog Content: {blog_content[:800]}...\n\nGenerate 15-20 specific, actionable checklist items organized by phase:\n\nPhase 1: Preparation (3-4 items)\nPhase 2: Implementation (5-7 items)\nPhase 3: Testing & Validation (3-4 items)\nPhase 4: Optimization (2-3 items)\nPhase 5: Maintenance (2-3 items)\n\nEach item should:\n- Be specific and actionable (not vague)\n- Include measurable criteria when possible\n- Be ordered logically\n- Include time estimates where applicable\n- Reference specific tools, commands, or configurations\n- Include success criteria or completion indicators"
                    }
                ]
            )
            
            content = response.choices[0].message.content.strip()
            # Parse into list, preserving phase structure
            items = []
            current_phase = ""
            for line in content.split('\n'):
                line = line.strip()
                if not line:
                    continue
                # Check if it's a phase header
                if line.startswith(('Phase', 'PHASE')) or ':' in line and len(line) < 50:
                    current_phase = line
                    items.append(f"--- {line} ---")
                else:
                    # It's a checklist item
                    item = line.lstrip('-•*123456789.').strip()
                    if item and not item.startswith('---'):
                        items.append(item)
            return items
        except Exception as e:
            logger.error(f"Error generating checklist: {e}")
            return []
    
    def _generate_templates(self, blog_title: str, blog_content: str) -> List[Dict]:
        """Generate production-ready templates or code snippets based on the content"""
        try:
            response = self.client.chat.completions.create(
                model=config.openai_model_digital_product,
                max_tokens=3000,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at creating production-ready templates and code snippets. Create reusable, well-documented, copy-paste ready templates that professionals can use immediately."
                    },
                    {
                        "role": "user",
                        "content": f"Create 5-7 production-ready templates or code snippets based on:\n\nBlog Title: {blog_title}\nBlog Content: {blog_content[:800]}...\n\nEach template should include:\n1. A clear, descriptive name\n2. The actual template/code (complete and ready to use)\n3. File name suggestion (if applicable)\n4. Prerequisites or dependencies\n5. Step-by-step usage instructions\n6. Customization options\n7. Common variations or alternatives\n8. Example output or expected result\n\nTemplate types to consider:\n- Configuration files\n- Code templates\n- Scripts or automation\n- Checklists or worksheets\n- Documentation templates\n- Testing templates\n- Deployment templates\n\nReturn each template in this format:\n\n## TEMPLATE NAME\n**File:** [filename]\n**Prerequisites:** [list]\n**Code/Content:**\n```\n[actual template content]\n```\n**Usage Instructions:**\n[step-by-step]\n**Customization Options:**\n[list]\n**Example Output:**\n[example]"
                    }
                ]
            )
            
            content = response.choices[0].message.content.strip()
            # Parse into structured format
            templates = []
            current_template = None
            current_field = None
            
            for line in content.split('\n'):
                line_stripped = line.strip()
                
                # Detect new template
                if line_stripped.startswith('##') or (line_stripped and line_stripped[0].isdigit() and '.' in line_stripped[:3]):
                    if current_template:
                        templates.append(current_template)
                    current_template = {
                        'name': line_stripped.replace('##', '').strip(),
                        'file': '',
                        'prerequisites': '',
                        'content': '',
                        'instructions': '',
                        'customization': '',
                        'example': ''
                    }
                    current_field = None
                elif current_template:
                    # Detect field headers
                    if line_stripped.lower().startswith('**file:**'):
                        current_field = 'file'
                        current_template['file'] = line_stripped.replace('**File:**', '').replace('**file:**', '').strip()
                    elif line_stripped.lower().startswith('**prerequisites:**'):
                        current_field = 'prerequisites'
                        current_template['prerequisites'] = line_stripped.replace('**Prerequisites:**', '').replace('**prerequisites:**', '').strip()
                    elif line_stripped.lower().startswith('**code/content:**'):
                        current_field = 'content'
                    elif line_stripped.lower().startswith('**usage instructions:**'):
                        current_field = 'instructions'
                    elif line_stripped.lower().startswith('**customization options:**'):
                        current_field = 'customization'
                    elif line_stripped.lower().startswith('**example output:**'):
                        current_field = 'example'
                    elif line_stripped.startswith('```'):
                        # Code block delimiter
                        if current_field == 'content':
                            current_field = 'code_block'
                        elif current_field == 'code_block':
                            current_field = 'content'
                    elif current_field:
                        # Add content to current field
                        if current_field == 'code_block':
                            current_template['content'] += line + '\n'
                        else:
                            if current_field in current_template:
                                current_template[current_field] += line + '\n'
            
            if current_template:
                templates.append(current_template)
            
            return templates
        except Exception as e:
            logger.error(f"Error generating templates: {e}")
            return []
    
    def _suggest_pricing(self, blog_niche: str, topic_demand: str = 'medium') -> float:
        """Suggest pricing based on niche, content value, and demand level"""
        # Base pricing by niche (higher for more technical/specialized niches)
        niche_pricing = {
            'software_development': 24.99,
            'programming': 19.99,
            'web_development': 22.99,
            'data_science': 29.99,
            'devops': 27.99,
            'machine_learning': 34.99,
            'cybersecurity': 32.99,
            'cloud_computing': 28.99,
            'mobile_development': 23.99,
            'default': 14.99
        }
        
        base_price = niche_pricing.get(blog_niche.lower().replace(' ', '_'), niche_pricing['default'])
        
        # Adjust based on demand level
        demand_multiplier = {
            'low': 0.8,
            'medium': 1.0,
            'high': 1.3,
            'very_high': 1.5
        }
        
        multiplier = demand_multiplier.get(topic_demand.lower(), 1.0)
        final_price = base_price * multiplier
        
        # Round to .99
        final_price = round(final_price, 0) - 0.01 if final_price >= 10 else round(final_price, 2)
        
        # Ensure minimum price of 0.99 (Gumroad requirement)
        final_price = max(final_price, 0.99)
        
        logger.info(f"Suggested pricing for {blog_niche} ({topic_demand} demand): ${final_price}")
        return final_price
    
    def _generate_functional_tools(self, blog_title: str, blog_content: str, blog_niche: str) -> List[Dict]:
        """Generate functional tools, plugins, or applications related to the topic"""
        try:
            response = self.client.chat.completions.create(
                model=config.openai_model_digital_product,
                max_tokens=config.max_tokens_digital_product,
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are an expert at creating functional, sellable digital tools, plugins, and applications for {blog_niche}. 

CRITICAL REQUIREMENTS:
- Keep tools SMALL and FOCUSED (50-200 lines of code maximum)
- Each tool should do ONE thing extremely well
- Avoid complex architectures that introduce bugs
- Use standard libraries when possible
- Include error handling for common edge cases
- Make code readable and maintainable
- Test the logic mentally before writing

Your goal is to create tools that:
- Solve real, painful problems professionals face
- Are not easily found for free online
- Provide immediate value and time savings
- Can be sold as premium products
- Include complete, working code that users can deploy immediately
- Are BUG-FREE and reliable

Focus on creating tools that users would happily pay for because they save hours of work or solve complex problems."""
                    },
                    {
                        "role": "user",
                        "content": f"""Based on this blog topic: {blog_title}

Blog content summary: {blog_content[:1000]}...

Generate 3-5 functional tools, plugins, or applications that professionals in this niche would pay for. These should be practical, working tools that solve real problems.

IMPORTANT: Keep each tool SMALL and FOCUSED (50-200 lines). Do not create large, complex applications. Focus on single-purpose tools that do one thing perfectly.

For each tool, provide:
1. **Tool Name**: Clear, descriptive name
2. **Type**: Script, Plugin, Extension, CLI Tool, Web App, Library, etc.
3. **Purpose**: What problem it solves and why it's valuable
4. **Target Users**: Who would use this and why they'd pay for it
5. **Language/Framework**: The tech stack (Python, JavaScript, etc.)
6. **Complete Code**: Full, working code with comments (50-200 lines MAX)
7. **Installation Instructions**: Step-by-step setup guide
8. **Usage Examples**: How to use the tool with examples
9. **Configuration**: Any config files or environment variables needed
10. **Dependencies**: Required packages/libraries with versions (keep minimal)
11. **Customization Guide**: How users can adapt it to their needs
12. **Monetization Value**: Why this is worth paying for (time saved, complexity handled, etc.)

Tool ideas to consider (keep them simple and focused):
- Automation scripts for repetitive tasks
- CLI tools for specific workflows
- Simple configuration generators
- Data validation/checking scripts
- Log parsing/analysis tools
- Simple monitoring/checking scripts
- File conversion utilities
- API wrapper scripts
- Template generators
- Simple testing utilities

Return the tools in this JSON format:
{{
  "tools": [
    {{
      "name": "Tool Name",
      "type": "Script/Plugin/App",
      "purpose": "Description",
      "target_users": "Who needs this",
      "language": "Python/JavaScript/etc",
      "code": "Complete working code here (50-200 lines)",
      "installation": "Step-by-step instructions",
      "usage": "Usage examples",
      "configuration": "Config details",
      "dependencies": ["package1==1.0.0"],
      "customization": "How to customize",
      "monetization_value": "Why this is worth paying for"
    }}
  ]
}}"""
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content.strip()
            result = json.loads(content)
            
            tools = result.get('tools', [])
            logger.info(f"Generated {len(tools)} functional tools")
            return tools
            
        except Exception as e:
            logger.error(f"Error generating functional tools: {e}")
            return []
    
    def _generate_marketing_copy(self, blog_title: str, blog_content: str) -> str:
        """Generate marketing copy for promoting the product"""
        try:
            response = self.client.chat.completions.create(
                model=config.openai_model_digital_product,
                max_tokens=300,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert marketing copywriter. Create compelling copy that drives conversions."
                    },
                    {
                        "role": "user",
                        "content": f"Create marketing copy for promoting a digital product based on:\n\nBlog Title: {blog_title}\nBlog Content: {blog_content[:300]}...\n\nThe copy should:\n- Be 150-200 words\n- Create excitement and urgency\n- Highlight the transformation the product provides\n- Include a clear call-to-action\n- Use power words and emotional triggers"
                    }
                ]
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating marketing copy: {e}")
            return f"Get the complete guide to {blog_title} - everything you need to succeed!"
    
    def save_product_files(self, product_data: Dict, blog_title: str) -> Dict:
        """Save all product files to a dedicated folder"""
        # Create safe folder name
        safe_title = "".join(c for c in blog_title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')
        
        product_folder = self.output_dir / safe_title
        product_folder.mkdir(parents=True, exist_ok=True)
        
        saved_files = {}
        
        # Gumroad receives an install-free application package, never a guide or loose script.
        app_folder = product_folder / "utility"
        app_folder.mkdir(parents=True, exist_ok=True)
        app_file = app_folder / "index.html"
        app_file.write_text(product_data['content'], encoding='utf-8')
        readme = app_folder / "README.txt"
        readme.write_text(
            f"{product_data['title']}\n\n{product_data.get('description', '')}\n\n"
            "Open index.html in any modern browser. The utility runs locally and needs no installation or account.\n",
            encoding='utf-8'
        )
        package_file = product_folder / "utility_package.zip"
        with zipfile.ZipFile(package_file, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.write(app_file, "utility/index.html")
            archive.write(readme, "utility/README.txt")
        saved_files['content'] = str(package_file)
        saved_files['package'] = str(package_file)
        
        metadata_file = product_folder / "product_metadata.json"
        metadata = {
            'title': product_data['title'],
            'description': product_data['description'],
            'pricing': product_data['pricing'],
            'quality_score': product_data.get('quality_score', 0),
            'demand_level': product_data.get('demand_level', 'medium'),
            'niche': product_data.get('niche', ''),
            'product_type': 'offline_browser_utility',
            'problem': product_data.get('problem', '')
        }
        metadata_file.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        saved_files['metadata'] = str(metadata_file)
        
        logger.info(f"Saved product files to: {product_folder}")
        saved_files['folder'] = str(product_folder)
        return saved_files
    
    def _get_extension(self, language: str) -> str:
        """Get file extension based on programming language"""
        extensions = {
            'python': 'py',
            'javascript': 'js',
            'typescript': 'ts',
            'java': 'java',
            'go': 'go',
            'rust': 'rs',
            'ruby': 'rb',
            'php': 'php',
            'shell': 'sh',
            'bash': 'sh',
            'powershell': 'ps1',
            'sql': 'sql',
            'html': 'html',
            'css': 'css',
            'json': 'json',
            'yaml': 'yaml',
            'yml': 'yml',
            'xml': 'xml',
            'markdown': 'md',
            'dockerfile': 'dockerfile',
            'docker': 'dockerfile'
        }
        language_lower = language.lower()
        return extensions.get(language_lower, 'txt')
