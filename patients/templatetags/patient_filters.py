from django import template
import re

register = template.Library()

@register.filter
def split_conditions(medical_history):
    """Extract medical conditions from medical history text"""
    if not medical_history or "Medical Conditions:" not in medical_history:
        return []
    
    # Find the line with medical conditions
    lines = medical_history.split('\n')
    for line in lines:
        if "Medical Conditions:" in line:
            # Extract the conditions part and split by comma
            conditions_part = line.split("Medical Conditions:")[1].strip()
            return [condition.strip() for condition in conditions_part.split(',')]
    
    return []

@register.filter
def remove_conditions(medical_history):
    """Remove the medical conditions line from the medical history"""
    if not medical_history or "Medical Conditions:" not in medical_history:
        return medical_history
    
    # Remove the line with medical conditions
    lines = medical_history.split('\n')
    filtered_lines = [line for line in lines if "Medical Conditions:" not in line]
    return '\n'.join(filtered_lines).strip()