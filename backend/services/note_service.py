"""
Note Service
Handles note creation, editing, and file management
"""

import os
from datetime import datetime
from database.database import Note
from sqlalchemy.orm import Session

class NoteService:
    def __init__(self):
        self.notes_dir = os.path.join(os.path.dirname(__file__), "..", "notes")
        os.makedirs(self.notes_dir, exist_ok=True)
    
    def create_note(self, db: Session, note_data: dict):
        """Create a new note"""
        title = note_data.get("title", "Untitled Note")
        content = note_data.get("content", "")
        
        # Create note in database
        note = Note(
            title=title,
            content=content
        )
        db.add(note)
        db.commit()
        db.refresh(note)
        
        # Save as .txt file
        file_path = os.path.join(self.notes_dir, f"note_{note.id}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"{title}\n\n{content}")
        
        note.file_path = file_path
        db.commit()
        
        return note
    
    def get_all_notes(self, db: Session):
        """Get all notes"""
        notes = db.query(Note).order_by(Note.created_at.desc()).all()
        return [
            {
                "id": n.id,
                "title": n.title,
                "content": n.content,
                "file_path": n.file_path,
                "created_at": n.created_at.isoformat(),
                "updated_at": n.updated_at.isoformat()
            }
            for n in notes
        ]
    
    def get_note(self, db: Session, note_id: int):
        """Get a specific note"""
        note = db.query(Note).filter(Note.id == note_id).first()
        if note:
            return {
                "id": note.id,
                "title": note.title,
                "content": note.content,
                "file_path": note.file_path,
                "created_at": note.created_at.isoformat(),
                "updated_at": note.updated_at.isoformat()
            }
        return None
    
    def update_note(self, db: Session, note_id: int, note_data: dict):
        """Update a note"""
        note = db.query(Note).filter(Note.id == note_id).first()
        if note:
            if "title" in note_data:
                note.title = note_data["title"]
            if "content" in note_data:
                note.content = note_data["content"]
            note.updated_at = datetime.utcnow()
            
            # Update .txt file
            if note.file_path and os.path.exists(note.file_path):
                with open(note.file_path, "w", encoding="utf-8") as f:
                    f.write(f"{note.title}\n\n{note.content}")
            
            db.commit()
            db.refresh(note)
        return note
    
    def delete_note(self, db: Session, note_id: int):
        """Delete a note"""
        note = db.query(Note).filter(Note.id == note_id).first()
        if note:
            # Delete .txt file
            if note.file_path and os.path.exists(note.file_path):
                os.remove(note.file_path)
            
            db.delete(note)
            db.commit()
        return note

