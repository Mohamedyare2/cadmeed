import os
import sys

def create_app():
    from flask import Flask, render_template, request, redirect, url_for, session, flash
    from dotenv import load_dotenv

    load_dotenv()

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, root_dir)

    template_dir = os.path.join(root_dir, 'templates')
    static_dir = os.path.join(root_dir, 'static')

    flask_app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    flask_app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-key-123")

    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "gacanka2026")

    def get_supabase():
        """Create supabase client lazily inside each request so env vars are ready."""
        from supabase import create_client
        url = os.environ.get("SUPABASE_URL", "").strip()
        key = os.environ.get("SUPABASE_KEY", "").strip()
        if not url or not key:
            return None
        try:
            return create_client(url, key)
        except Exception:
            return None

    @flask_app.route('/debug-env')
    def debug_env():
        from supabase import create_client
        url = os.environ.get("SUPABASE_URL", "MISSING").strip()
        key = os.environ.get("SUPABASE_KEY", "MISSING").strip()
        key_preview = f"{key[:25]}...{key[-25:]}" if len(key) > 50 else key
        try:
            import supabase as sb_module
            ver = getattr(sb_module, '__version__', 'unknown')
        except Exception:
            ver = "error"
        try:
            client = create_client(url, key)
            result = f"SUCCESS ({type(client).__name__})"
        except Exception as ex:
            result = f"FAILED: {repr(ex)}"
        return f"""
        <h2>Live Debug Info</h2>
        <p><b>URL:</b> {url}</p>
        <p><b>KEY (preview):</b> {key_preview}</p>
        <p><b>KEY length:</b> {len(key)}</p>
        <p><b>KEY starts with eyJ:</b> {key.startswith('eyJ')}</p>
        <p><b>supabase-py version:</b> {ver}</p>
        <p><b>Direct create_client test:</b> {result}</p>
        """

    @flask_app.route('/')
    def index():
        return render_template('index.html')

    @flask_app.route('/services')
    def services():
        return render_template('services.html')

    @flask_app.route('/gallery')
    def gallery():
        supabase = get_supabase()
        projects = []
        if supabase:
            try:
                response = supabase.table('projects').select('*, project_images(image_url)').order('created_at', desc=True).execute()
                projects = response.data
            except Exception:
                pass
        return render_template('gallery.html', projects=projects, db_connected=bool(supabase))

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

        supabase = get_supabase()

        if not supabase:
            flash("Supabase not configured correctly. Check your API key. Projects cannot be saved.")
            return render_template('admin.html')

        if request.method == 'POST':
            try:
                name = request.form.get('name')
                client_name = request.form.get('client')
                city = request.form.get('city')
                description = request.form.get('description')
                images = request.files.getlist('images')

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

                        # Check if storage bucket exists or handle upload explicitly (might crash if bucket is missing)
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
            except Exception as e:
                flash(f"Error saving project: {str(e)}")
                # Fall through to render admin.html

        return render_template('admin.html')

    @flask_app.route('/edit/<project_id>', methods=['GET', 'POST'])
    def edit_project(project_id):
        if not session.get('admin_logged_in'):
            return redirect(url_for('login'))
        supabase = get_supabase()
        if not supabase:
            flash("Database not connected.")
            return redirect(url_for('gallery'))
        if request.method == 'POST':
            try:
                supabase.table('projects').update({
                    'name': request.form.get('name'),
                    'client': request.form.get('client'),
                    'city': request.form.get('city'),
                    'description': request.form.get('description')
                }).eq('id', project_id).execute()
                flash("Project updated successfully!")
            except Exception as e:
                flash(f"Error: {str(e)}")
            return redirect(url_for('gallery'))
        try:
            response = supabase.table('projects').select('*').eq('id', project_id).execute()
            if response.data:
                return render_template('edit_project.html', project=response.data[0])
        except Exception:
            pass
        flash("Project not found.")
        return redirect(url_for('gallery'))

    @flask_app.route('/delete/<project_id>', methods=['POST'])
    def delete_project(project_id):
        if not session.get('admin_logged_in'):
            return redirect(url_for('login'))
        supabase = get_supabase()
        if not supabase:
            flash("Database not connected.")
            return redirect(url_for('gallery'))
        try:
            supabase.table('projects').delete().eq('id', project_id).execute()
            flash("Project deleted successfully!")
        except Exception as e:
            flash(f"Error: {str(e)}")
        return redirect(url_for('gallery'))

    return flask_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
