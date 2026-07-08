import os
import sys
import traceback

def create_app():
    try:
        from flask import Flask, render_template, request, redirect, url_for, session, flash
        from supabase import create_client, Client
        from dotenv import load_dotenv

        load_dotenv()

        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, root_dir)

        template_dir = os.path.join(root_dir, 'templates')
        static_dir = os.path.join(root_dir, 'static')

        flask_app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
        flask_app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-key-123")

        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")

        supabase = None
        if url and key:
            supabase = create_client(url, key)

        ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
        ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "gacanka2026")

        @flask_app.route('/')
        def index():
            return render_template('index.html')

        @flask_app.route('/services')
        def services():
            return render_template('services.html')

        @flask_app.route('/gallery')
        def gallery():
            projects = []
            if supabase:
                response = supabase.table('projects').select('*, project_images(image_url)').order('created_at', desc=True).execute()
                projects = response.data
            return render_template('gallery.html', projects=projects)

        @flask_app.route('/login', methods=['GET', 'POST'])
        def login():
            if request.method == 'POST':
                username = request.form.get('username')
                password = request.form.get('password')
                if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                    session['admin_logged_in'] = True
                    return redirect(url_for('admin'))
                else:
                    flash("Invalid Credentials")
            return render_template('login.html')

        @flask_app.route('/logout')
        def logout():
            session.pop('admin_logged_in', None)
            return redirect(url_for('index'))

        @flask_app.route('/admin', methods=['GET', 'POST'])
        def admin():
            if not session.get('admin_logged_in'):
                return redirect(url_for('login'))

            if request.method == 'POST':
                name = request.form.get('name')
                client_name = request.form.get('client')
                city = request.form.get('city')
                description = request.form.get('description')
                images = request.files.getlist('images')

                if not supabase:
                    flash("Supabase not configured. Please set environment variables.")
                    return redirect(url_for('admin'))

                response = supabase.table('projects').insert({
                    'name': name,
                    'client': client_name,
                    'city': city,
                    'description': description
                }).execute()

                project_id = response.data[0]['id']

                for i, file in enumerate(images):
                    if file and file.filename:
                        file_ext = file.filename.rsplit('.', 1)[-1].lower()
                        file_name = f"{project_id}_{i}.{file_ext}"
                        file_bytes = file.read()

                        supabase.storage.from_("gallery").upload(
                            file_name,
                            file_bytes,
                            {"content-type": f"image/{file_ext}"}
                        )

                        public_url = supabase.storage.from_("gallery").get_public_url(file_name)

                        supabase.table('project_images').insert({
                            'project_id': project_id,
                            'image_url': public_url
                        }).execute()

                flash("Project added successfully!")
                return redirect(url_for('gallery'))

            return render_template('admin.html')
            
        return flask_app

    except Exception as e:
        error_msg = traceback.format_exc()
        # Fallback simplistic app
        from flask import Flask
        fallback_app = Flask(__name__)
        @fallback_app.route('/', defaults={'path': ''})
        @fallback_app.route('/<path:path>')
        def catch_all(path):
            return f"<h1>App Crashed on Startup</h1><pre>{error_msg}</pre>", 500
        return fallback_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)

