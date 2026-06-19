import os
from app import create_app
from app.models import db

app = create_app()

def initialize_database():
    print("Initializing database...")
    with app.app_context():
        # Ensure instance directory exists (for SQLite)
        instance_dir = os.path.join(app.root_path, '..', 'instance')
        if not os.path.exists(instance_dir):
            os.makedirs(instance_dir)
            print(f"Created instance directory at: {instance_dir}")
            
        # Ensure upload folder exists
        upload_folder = app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
            print(f"Created upload directory at: {upload_folder}")

        # Ensure database tables are created
        db.create_all()
        print("Database tables created successfully.")
            
    print("Initialization completed successfully!")

if __name__ == '__main__':
    initialize_database()
