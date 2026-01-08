"""
Knowledge Graph extraction and visualization for AI Partner Runner.
Extracts entities and relationships from notes and builds a knowledge graph.
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict


class KnowledgeGraphBuilder:
    """Build knowledge graph from notes using entity extraction and relationship detection."""
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.kg_dir = workspace / "knowledge_graph"
        self.kg_dir.mkdir(parents=True, exist_ok=True)
        self.entities: Dict[str, Dict[str, Any]] = {}
        self.relationships: List[Dict[str, Any]] = []
        
    def extract_entities(self, text: str, filename: str) -> List[Dict[str, str]]:
        """
        Extract entities from text using simple pattern matching.
        In production, this could use NER models or LLM-based extraction.
        """
        entities = []
        
        # Common entity patterns (Chinese and English)
        patterns = {
            'person': [
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # English names
                r'([\u4e00-\u9fa5]{2,4})',  # Chinese names (2-4 chars)
            ],
            'organization': [
                r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s+(?:Inc|Corp|Ltd|Company|Co))',
                r'([\u4e00-\u9fa5]+(?:公司|企业|集团|机构|组织))',
            ],
            'location': [
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:City|State|Country|Province))',
                r'([\u4e00-\u9fa5]+(?:市|省|县|区|国))',
            ],
            'technology': [
                r'([A-Z][a-zA-Z]*(?:\.js|\.py|\.ts|\.java|\.go|\.rs))',  # File extensions
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Framework|Library|Tool|Platform))',
                r'([\u4e00-\u9fa5]+(?:框架|库|工具|平台|系统))',
            ],
            'concept': [
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # Capitalized phrases
                r'([\u4e00-\u9fa5]{3,})',  # Chinese concepts (3+ chars)
            ],
        }
        
        for entity_type, type_patterns in patterns.items():
            for pattern in type_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    entity_text = match.group(1).strip()
                    if len(entity_text) >= 2:  # Filter very short matches
                        entities.append({
                            'text': entity_text,
                            'type': entity_type,
                            'start': match.start(),
                            'end': match.end(),
                            'source_file': filename,
                        })
        
        return entities
    
    def detect_relationships(self, entities: List[Dict[str, str]], text: str) -> List[Dict[str, Any]]:
        """
        Detect relationships between entities based on proximity and context.
        """
        relationships = []
        
        # Relationship keywords
        relation_keywords = {
            'uses': ['使用', 'uses', 'utilizes', 'employs', '采用'],
            'implements': ['实现', 'implements', 'builds', 'creates', '开发'],
            'related_to': ['相关', 'related', 'associated', 'connected', '关联'],
            'part_of': ['属于', 'part of', 'member of', '包含在'],
            'depends_on': ['依赖', 'depends on', 'requires', 'needs', '需要'],
        }
        
        # Find entities that appear near each other (within 100 chars)
        for i, e1 in enumerate(entities):
            for j, e2 in enumerate(entities[i+1:], start=i+1):
                distance = abs(e1['start'] - e2['start'])
                if distance < 100:  # Entities are close
                    # Check for relationship keywords between them
                    start = min(e1['start'], e2['start'])
                    end = max(e1['end'], e2['end'])
                    context = text[max(0, start-20):min(len(text), end+20)]
                    
                    relation_type = None
                    for rel_type, keywords in relation_keywords.items():
                        if any(kw in context.lower() for kw in keywords):
                            relation_type = rel_type
                            break
                    
                    if not relation_type:
                        relation_type = 'related_to'  # Default
                    
                    relationships.append({
                        'source': e1['text'],
                        'target': e2['text'],
                        'type': relation_type,
                        'source_type': e1['type'],
                        'target_type': e2['type'],
                        'context': context[:50],
                    })
        
        return relationships
    
    def build_from_notes(self) -> Dict[str, Any]:
        """Build knowledge graph from all notes in workspace."""
        notes_dir = self.workspace / "notes"
        if not notes_dir.exists():
            return {'entities': {}, 'relationships': []}
        
        all_entities = []
        all_relationships = []
        entity_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # Process each note file
        for note_file in notes_dir.glob("**/*"):
            if note_file.is_file() and note_file.suffix in ['.md', '.txt']:
                try:
                    text = note_file.read_text(encoding="utf-8", errors="ignore")
                    filename = note_file.name
                    
                    # Extract entities
                    entities = self.extract_entities(text, filename)
                    all_entities.extend(entities)
                    
                    # Detect relationships
                    relationships = self.detect_relationships(entities, text)
                    all_relationships.extend(relationships)
                    
                    # Count entity occurrences
                    for entity in entities:
                        entity_counts[entity['text']][entity['type']] += 1
                except Exception as e:
                    print(f"Error processing {note_file}: {e}")
                    continue
        
        # Consolidate entities (merge duplicates)
        consolidated_entities = {}
        for entity in all_entities:
            text = entity['text']
            if text not in consolidated_entities:
                consolidated_entities[text] = {
                    'id': text,
                    'label': text,
                    'type': entity['type'],
                    'count': entity_counts[text].get(entity['type'], 1),
                    'files': set([entity['source_file']]),
                }
            else:
                consolidated_entities[text]['count'] += 1
                consolidated_entities[text]['files'].add(entity['source_file'])
        
        # Convert sets to lists for JSON serialization
        for entity in consolidated_entities.values():
            entity['files'] = list(entity['files'])
        
        # Deduplicate relationships
        seen_rels = set()
        unique_relationships = []
        for rel in all_relationships:
            key = (rel['source'], rel['target'], rel['type'])
            if key not in seen_rels:
                seen_rels.add(key)
                unique_relationships.append(rel)
        
        self.entities = consolidated_entities
        self.relationships = unique_relationships
        
        return {
            'entities': consolidated_entities,
            'relationships': unique_relationships,
        }
    
    def save_graph(self) -> Path:
        """Save knowledge graph to JSON file."""
        kg_data = {
            'entities': self.entities,
            'relationships': self.relationships,
        }
        
        kg_file = self.kg_dir / "graph.json"
        with open(kg_file, 'w', encoding='utf-8') as f:
            json.dump(kg_data, f, ensure_ascii=False, indent=2)
        
        return kg_file
    
    def get_graph_for_visualization(self) -> Dict[str, Any]:
        """Get graph data in format suitable for frontend visualization (D3.js/vis.js)."""
        nodes = []
        links = []
        
        # Create nodes from entities
        for entity_id, entity_data in self.entities.items():
            nodes.append({
                'id': entity_id,
                'label': entity_data['label'],
                'type': entity_data['type'],
                'size': min(entity_data['count'] * 2, 50),  # Scale node size
                'files': entity_data.get('files', []),
            })
        
        # Create links from relationships
        for rel in self.relationships:
            links.append({
                'source': rel['source'],
                'target': rel['target'],
                'type': rel['type'],
                'value': 1,
            })
        
        return {
            'nodes': nodes,
            'links': links,
        }

