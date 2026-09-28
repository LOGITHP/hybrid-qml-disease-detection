import os
import re

models_dir = r"c:\Users\logit\Downloads\hybrid-qml-disease-detection\Diseases_Detection_Paltform\backend\app\database\models"

def migrate_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Replace imports
    content = re.sub(r'from sqlalchemy.*?\n', '', content)
    content = re.sub(r'from app\.database\.base.*?\n', 'from beanie import Document, Link\nfrom pydantic import Field\nfrom datetime import datetime, timezone\nimport uuid\n', content)

    # Replace class definitions
    content = re.sub(r'class (\w+)\(Base, UUIDPrimaryKeyMixin, TimestampMixin\):', r'class \1(Document):', content)
    
    # Replace table names
    content = re.sub(r'__tablename__ = "(.*?)"', r'class Settings:\n        name = "\1"', content)

    # Replace Mapped columns
    content = re.sub(r'([a-zA-Z_]+): Mapped\[Optional\[(.*?)\]\] = mapped_column\(.*?\)', r'\1: \2 | None = None', content)
    content = re.sub(r'([a-zA-Z_]+): Mapped\[(.*?)\] = mapped_column\(.*?(default=(.*?)).*?\)', r'\1: \2 = \4', content)
    content = re.sub(r'([a-zA-Z_]+): Mapped\[(.*?)\] = mapped_column\(.*?\)', r'\1: \2', content)

    # Relationships are dropped for now to be handled manually or kept as string references
    content = re.sub(r'([a-zA-Z_]+) = relationship\(.*?\)\n', '', content)

    # Add timestamp defaults
    timestamp_fields = """
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
"""
    # Insert timestamp fields before Settings
    content = re.sub(r'(class Settings:)', r'    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))\n    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))\n\n    \1', content)

    with open(filepath, 'w') as f:
        f.write(content)

for root, _, files in os.walk(models_dir):
    for file in files:
        if file.endswith('.py') and file != '__init__.py':
            migrate_file(os.path.join(root, file))

print("Models migrated.")
