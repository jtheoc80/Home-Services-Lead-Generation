#!/usr/bin/env python3
"""
Email and SMS template rendering utilities for subscription notifications.

This module provides functionality to render email and SMS templates with
context data for various subscription events like cancellation, reactivation, etc.
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Template directories
TEMPLATE_BASE_DIR = Path(__file__).parent.parent / "templates"
EMAIL_TEMPLATE_DIR = TEMPLATE_BASE_DIR / "email"
SMS_TEMPLATE_DIR = TEMPLATE_BASE_DIR / "sms"


class TemplateRenderer:
    """Template renderer for email and SMS notifications."""
    
    def __init__(self, brand_name: str = None, base_url: str = None):
        self.brand_name = brand_name or os.getenv('EMAIL_BRAND', 'LeadLedgerPro')
        self.base_url = base_url or os.getenv('BASE_URL', 'https://leadledgerpro.com')
        
        # Try to import Jinja2 for advanced templating
        try:
            from jinja2 import Environment, FileSystemLoader, select_autoescape
            self.jinja_env = Environment(
                loader=FileSystemLoader([str(EMAIL_TEMPLATE_DIR), str(SMS_TEMPLATE_DIR)]),
                autoescape=select_autoescape(['html', 'xml'])
            )
            self.use_jinja = True
            logger.info("Using Jinja2 for template rendering")
        except ImportError:
            self.jinja_env = None
            self.use_jinja = False
            logger.warning("Jinja2 not available, using simple string formatting")
    
    def _get_common_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Add common template variables to context."""
        now = datetime.now()
        
        common_context = {
            'brand_name': self.brand_name,
            'current_date': now.strftime('%Y-%m-%d'),
            'current_year': now.year,
            'settings_url': f"{self.base_url}/settings/subscription",
            'dashboard_url': f"{self.base_url}/dashboard",
            'signup_url': f"{self.base_url}/signup",
            'billing_url': f"{self.base_url}/settings/billing",
            'help_url': f"{self.base_url}/help",
        }
        
        # Add date formatting helpers
        if 'effective_at' in context:
            try:
                if isinstance(context['effective_at'], str):
                    effective_date = datetime.fromisoformat(context['effective_at'].replace('Z', '+00:00'))
                else:
                    effective_date = context['effective_at']
                
                common_context.update({
                    'effective_date': effective_date.strftime('%B %d, %Y'),
                    'effective_date_short': effective_date.strftime('%m/%d/%Y'),
                    'is_immediate': effective_date <= now
                })
            except (ValueError, AttributeError) as e:
                logger.warning(f"Error parsing effective_at date: {e}")
        
        if 'reactivated_at' in context:
            try:
                if isinstance(context['reactivated_at'], str):
                    reactivated_date = datetime.fromisoformat(context['reactivated_at'].replace('Z', '+00:00'))
                else:
                    reactivated_date = context['reactivated_at']
                
                common_context.update({
                    'reactivated_date': reactivated_date.strftime('%B %d, %Y'),
                    'next_billing_date': (reactivated_date.replace(month=reactivated_date.month + 1) 
                                        if reactivated_date.month < 12 
                                        else reactivated_date.replace(year=reactivated_date.year + 1, month=1)).strftime('%B %d, %Y')
                })
            except (ValueError, AttributeError) as e:
                logger.warning(f"Error parsing reactivated_at date: {e}")
        
        # Merge with provided context (user context takes precedence)
        return {**common_context, **context}
    
    def _render_template_simple(self, template_content: str, context: Dict[str, Any]) -> str:
        """Simple template rendering using string formatting."""
        try:
            # Use string formatting with context
            return template_content.format(**context)
        except KeyError as e:
            logger.error(f"Missing template variable: {e}")
            return template_content
        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            return template_content
    
    def _render_template_jinja(self, template_name: str, context: Dict[str, Any]) -> str:
        """Advanced template rendering using Jinja2."""
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Error rendering Jinja2 template {template_name}: {e}")
            # Fallback to simple rendering
            template_path = EMAIL_TEMPLATE_DIR / template_name
            if not template_path.exists():
                template_path = SMS_TEMPLATE_DIR / template_name
            
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return self._render_template_simple(content, context)
            
            return f"Template {template_name} not found"
    
    def render_email(self, template_name: str, context: Dict[str, Any]) -> Dict[str, str]:
        """
        Render an email template.
        
        Args:
            template_name: Name of the email template (without .md extension)
            context: Context variables for template rendering
            
        Returns:
            Dictionary with 'subject', 'text_content', and 'html_content' keys
        """
        full_context = self._get_common_context(context)
        template_file = f"{template_name}.md"
        
        if self.use_jinja and self.jinja_env:
            content = self._render_template_jinja(template_file, full_context)
        else:
            template_path = EMAIL_TEMPLATE_DIR / template_file
            if not template_path.exists():
                logger.error(f"Email template not found: {template_path}")
                return {
                    'subject': f"Notification from {self.brand_name}",
                    'text_content': f"Template {template_name} not found",
                    'html_content': f"<p>Template {template_name} not found</p>"
                }
            
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            content = self._render_template_simple(content, full_context)
        
        # Extract subject from first line if it starts with #
        lines = content.split('\n')
        subject = f"Notification from {self.brand_name}"
        
        if lines and lines[0].startswith('# '):
            subject = lines[0][2:].strip()
            content = '\n'.join(lines[1:]).strip()
        
        # Convert Markdown to HTML (basic conversion)
        html_content = self._markdown_to_html(content)
        
        return {
            'subject': subject,
            'text_content': content,
            'html_content': html_content
        }
    
    def render_sms(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render an SMS template.
        
        Args:
            template_name: Name of the SMS template (without .txt extension)
            context: Context variables for template rendering
            
        Returns:
            Rendered SMS message string
        """
        full_context = self._get_common_context(context)
        template_file = f"{template_name}.txt"
        
        if self.use_jinja and self.jinja_env:
            return self._render_template_jinja(template_file, full_context)
        else:
            template_path = SMS_TEMPLATE_DIR / template_file
            if not template_path.exists():
                logger.error(f"SMS template not found: {template_path}")
                return f"{self.brand_name}: Notification (template not found)"
            
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self._render_template_simple(content, full_context)
    
    def _markdown_to_html(self, markdown_content: str) -> str:
        """
        Basic Markdown to HTML conversion.
        
        For more advanced conversion, install python-markdown package.
        """
        try:
            import markdown
            return markdown.markdown(markdown_content)
        except ImportError:
            # Basic conversion without markdown library
            html = markdown_content
            
            # Convert headers
            html = html.replace('## ', '<h2>').replace('\n', '</h2>\n', 1) if '## ' in html else html
            html = html.replace('# ', '<h1>').replace('\n', '</h1>\n', 1) if '# ' in html else html
            
            # Convert bold
            import re
            html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
            
            # Convert line breaks to HTML
            html = html.replace('\n\n', '</p><p>').replace('\n', '<br>')
            html = f"<p>{html}</p>"
            
            # Clean up empty paragraphs
            html = html.replace('<p></p>', '').replace('<p><br></p>', '')
            
            return html


# Global renderer instance
_renderer = None

def get_renderer() -> TemplateRenderer:
    """Get the global template renderer instance."""
    global _renderer
    if _renderer is None:
        _renderer = TemplateRenderer()
    return _renderer

def render_email(template_name: str, context: Dict[str, Any]) -> Dict[str, str]:
    """
    Convenience function to render an email template.
    
    Args:
        template_name: Name of the email template
        context: Context variables for template rendering
        
    Returns:
        Dictionary with rendered email content
    """
    return get_renderer().render_email(template_name, context)

def render_sms(template_name: str, context: Dict[str, Any]) -> str:
    """
    Convenience function to render an SMS template.
    
    Args:
        template_name: Name of the SMS template
        context: Context variables for template rendering
        
    Returns:
        Rendered SMS message string
    """
    return get_renderer().render_sms(template_name, context)