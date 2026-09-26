from app.database import SessionLocal
from app.models import Project, Competitor, Post, ScrapeJob, TrendSnapshot, GeneratedIdea, Keyword

QA_PROJECT_ID = "708f72cf-5e1d-455c-b7c5-7d73e54209ce"

def delete_qa_project():
    db = SessionLocal()

    steps = [
        (GeneratedIdea, "generated_ideas"),
        (TrendSnapshot, "trend_snapshots"),
        (ScrapeJob, "scrape_jobs"),
        (Keyword, "keywords"),
        (Post, "posts"),
        (Competitor, "competitors"),
    ]

    for model, label in steps:
        count = db.query(model).filter(model.project_id == QA_PROJECT_ID).delete()
        print(f"Deleted {count} rows from {label}")
        db.commit()

    project = db.query(Project).filter(Project.id == QA_PROJECT_ID).first()
    if project:
        db.delete(project)
        db.commit()
        print(f"Deleted project: {project.name}")
    else:
        print("Project not found — may already be deleted")

    db.close()

if __name__ == "__main__":
    delete_qa_project()
