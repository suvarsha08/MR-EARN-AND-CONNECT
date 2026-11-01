import os
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, g, jsonify, abort
)
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db_connection, query_db, execute_db

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'mr_earn_and_connect_mrdu_tirupati_key_2026')

# -------------------------------------------------------------------
# HELPER FUNCTIONS & DECORATORS
# -------------------------------------------------------------------

def get_current_user():
    """Fetches currently logged-in user from session."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    user = query_db("SELECT id, name, email, role, phone, avatar FROM users WHERE id = ?", (user_id,), one=True)
    return user

@app.before_request
def load_logged_in_user():
    g.user = get_current_user()

@app.context_processor
def inject_globals():
    """Make current_user and helper context globally available in Jinja templates."""
    unread_announcements = query_db("SELECT COUNT(*) as cnt FROM announcements", one=True)
    return {
        'current_user': g.user,
        'announcement_count': unread_announcements['cnt'] if unread_announcements else 0,
        'now': datetime.now()
    }

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if g.user is None:
                flash("Please log in to continue.", "warning")
                return redirect(url_for('login'))
            if g.user['role'] not in allowed_roles and g.user['role'] != 'admin':
                flash("You do not have permission to access this section.", "danger")
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# -------------------------------------------------------------------
# TRANSPARENT SKILL & PROFILE ANALYSIS (NO AI)
# -------------------------------------------------------------------

def analyze_skill_compatibility(student_skills_list, required_skills_str):
    """
    Transparent, explainable Python logic - NO AI.
    Compares student's verified skills against required skills string.
    Returns:
      percentage: integer (0-100)
      matched: list of matched skills (formatted)
      missing: list of missing skills ("Skills to Develop")
      total_required: integer count
    """
    if not required_skills_str:
        return {"percentage": 100, "matched": [], "missing": [], "total_required": 0}
    
    req_skills = [s.strip() for s in required_skills_str.split(",") if s.strip()]
    if not req_skills:
        return {"percentage": 100, "matched": [], "missing": [], "total_required": 0}

    # Normalize student skills
    stud_norm = {}
    for s in student_skills_list:
        clean = s.strip().lower()
        if clean:
            stud_norm[clean] = s.strip()

    matched = []
    missing = []

    for req in req_skills:
        r_clean = req.lower()
        found = False
        # Direct or substring match
        for s_low, s_orig in stud_norm.items():
            if r_clean == s_low or r_clean in s_low or s_low in r_clean:
                matched.append(req.title())
                found = True
                break
        if not found:
            missing.append(req.title())

    total = len(req_skills)
    score = int((len(matched) / total) * 100) if total > 0 else 100

    return {
        "percentage": score,
        "matched": matched,
        "missing": missing,
        "total_required": total
    }

def calculate_profile_completion(user_id):
    """
    Computes transparent profile completion percentage (0-100%) and itemized breakdown:
    - Basic Information (Name, Email, Phone): 15%
    - Academic Details (College, Department, Course, Year): 15%
    - Bio / About Me: 10%
    - Skills (at least 3 skills): 20%
    - Projects (at least 1 project): 15%
    - Achievements / Certifications (at least 1): 15%
    - Career Preferences / Resume (Job type, Location, Resume link): 10%
    """
    user = query_db("SELECT * FROM users WHERE id = ?", (user_id,), one=True)
    profile = query_db("SELECT * FROM student_profiles WHERE user_id = ?", (user_id,), one=True)
    skills = query_db("SELECT * FROM skills WHERE student_id = ?", (user_id,))
    projects = query_db("SELECT * FROM projects WHERE student_id = ?", (user_id,))
    achievements = query_db("SELECT * FROM achievements WHERE student_id = ?", (user_id,))

    breakdown = []
    score = 0

    # 1. Basic Info (15%)
    has_basic = bool(user and user['name'] and user['email'] and user['phone'])
    basic_pts = 15 if has_basic else 5
    score += basic_pts
    breakdown.append({"title": "Basic Information (Name, Email, Phone)", "points": basic_pts, "max": 15, "completed": has_basic})

    # 2. Academic Info (15%)
    has_academic = bool(profile and profile['department'] and profile['course'] and profile['year'])
    acad_pts = 15 if has_academic else (8 if (profile and profile['department']) else 0)
    score += acad_pts
    breakdown.append({"title": "Academic Details (College, Dept, Course, Year)", "points": acad_pts, "max": 15, "completed": has_academic})

    # 3. Bio / About Me (10%)
    has_bio = bool(profile and profile['bio'] and len(profile['bio'].strip()) > 20)
    bio_pts = 10 if has_bio else 0
    score += bio_pts
    breakdown.append({"title": "About Me & Professional Bio", "points": bio_pts, "max": 10, "completed": has_bio})

    # 4. Skills (20%)
    skill_count = len(skills)
    skill_pts = 20 if skill_count >= 3 else (skill_count * 6)
    score += skill_pts
    breakdown.append({"title": f"Documented Skills ({skill_count} added, target 3+)", "points": skill_pts, "max": 20, "completed": skill_count >= 3})

    # 5. Projects (15%)
    proj_count = len(projects)
    proj_pts = 15 if proj_count >= 1 else 0
    score += proj_pts
    breakdown.append({"title": f"Student Projects Showcase ({proj_count} added)", "points": proj_pts, "max": 15, "completed": proj_count >= 1})

    # 6. Achievements / Awards (15%)
    ach_count = len(achievements)
    ach_pts = 15 if ach_count >= 1 else 0
    score += ach_pts
    breakdown.append({"title": f"Achievements & Certifications ({ach_count} added)", "points": ach_pts, "max": 15, "completed": ach_count >= 1})

    # 7. Resume & Preferences (10%)
    has_pref = bool(profile and (profile['resume'] or profile['preferred_job_type'] or profile['preferred_location']))
    pref_pts = 10 if has_pref else 0
    score += pref_pts
    breakdown.append({"title": "Resume Link & Job Preferences", "points": pref_pts, "max": 10, "completed": has_pref})

    final_score = min(score, 100)
    return {
        "percentage": final_score,
        "breakdown": breakdown,
        "skill_count": skill_count,
        "proj_count": proj_count,
        "ach_count": ach_count
    }

# -------------------------------------------------------------------
# AUTHENTICATION & DEMO LOGIN
# -------------------------------------------------------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if g.user:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        phone = request.form.get('phone', '').strip()
        role = request.form.get('role', 'student').strip()
        company_name = request.form.get('company_name', '').strip()

        if not name or not email or not password or not role:
            flash("Please fill in all required fields.", "danger")
            return render_template('register.html')

        if role not in ['student', 'employer', 'customer']:
            role = 'student'

        # Check duplicate email
        existing = query_db("SELECT id FROM users WHERE email = ?", (email,), one=True)
        if existing:
            flash("An account with this email address already exists. Please login.", "warning")
            return redirect(url_for('login'))

        hashed_pw = generate_password_hash(password)
        try:
            user_id = execute_db(
                "INSERT INTO users (name, email, password, role, phone) VALUES (?, ?, ?, ?, ?)",
                (name, email, hashed_pw, role, phone)
            )

            if role == 'student':
                execute_db(
                    "INSERT INTO student_profiles (user_id, college, department, course, year, bio) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, "Malla Reddy Deemed to be University, Tirupati", "Computer Science & Engineering", "B.Tech CSE-AIML", "1st Year", f"Hello! I am {name}, excited to learn, connect, and earn on MR EARN & CONNECT.")
                )
            elif role == 'employer':
                c_name = company_name if company_name else f"{name}'s Organization"
                execute_db(
                    "INSERT INTO companies (user_id, company_name, description, location) VALUES (?, ?, ?, ?)",
                    (user_id, c_name, "Innovative enterprise seeking talented students from MRDU Tirupati.", "Tirupati / Hybrid")
                )

            session['user_id'] = user_id
            session['user_name'] = name
            session['user_role'] = role
            flash(f"Welcome to MR EARN & CONNECT, {name}! Your {role.title()} account was created successfully.", "success")
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f"Registration could not be completed. Error: {str(e)}", "danger")

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = query_db("SELECT * FROM users WHERE email = ?", (email,), one=True)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_role'] = user['role']
            flash(f"Welcome back, {user['name']}!", "success")
            next_url = request.args.get('next')
            return redirect(next_url or url_for('dashboard'))
        else:
            flash("Invalid email or password. Please try again or use the 1-Click Demo Login below.", "danger")

    return render_template('login.html')

@app.route('/demo-login/<role>')
def demo_login(role):
    """
    1-Click instant login for live Ideathon judge presentations.
    Supported roles: student, employer, customer, admin.
    """
    demo_emails = {
        'student': 'arjun@student.mrdu.edu',
        'employer': 'techcorp@company.com',
        'customer': 'sharma@faculty.mrdu.edu',
        'admin': 'admin@mrearn.mrdu.edu'
    }
    target_email = demo_emails.get(role)
    if not target_email:
        flash("Unknown demo account role.", "warning")
        return redirect(url_for('login'))

    user = query_db("SELECT * FROM users WHERE email = ?", (target_email,), one=True)
    if user:
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_role'] = user['role']
        flash(f"⚡ Demo Login: Switched to {user['name']} ({user['role'].title()})!", "info")
        return redirect(url_for('dashboard'))
    else:
        flash("Demo account not found in database. Please run seed data.", "danger")
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for('index'))

# -------------------------------------------------------------------
# PUBLIC HOME & LANDING PAGE
# -------------------------------------------------------------------

@app.route('/')
def index():
    # Fetch real counts from SQLite database
    student_count = query_db("SELECT COUNT(*) as cnt FROM users WHERE role = 'student'", one=True)['cnt']
    job_count = query_db("SELECT COUNT(*) as cnt FROM jobs", one=True)['cnt']
    internship_count = query_db("SELECT COUNT(*) as cnt FROM internships", one=True)['cnt']
    service_count = query_db("SELECT COUNT(*) as cnt FROM services", one=True)['cnt']

    # Latest Featured Content
    featured_jobs = query_db("""
        SELECT j.*, c.company_name, c.logo 
        FROM jobs j 
        JOIN companies c ON j.company_id = c.id 
        ORDER BY j.id DESC LIMIT 4
    """)
    featured_services = query_db("""
        SELECT s.*, u.name as provider_name, u.avatar,
               COALESCE((SELECT AVG(rating) FROM ratings WHERE provider_id = s.provider_id), 5.0) as avg_rating,
               (SELECT COUNT(*) FROM ratings WHERE provider_id = s.provider_id) as review_count
        FROM services s 
        JOIN users u ON s.provider_id = u.id 
        WHERE s.availability = 'Available'
        ORDER BY s.id DESC LIMIT 4
    """)
    recent_announcements = query_db("SELECT * FROM announcements ORDER BY id DESC LIMIT 3")

    return render_template('index.html',
        student_count=student_count,
        job_count=job_count,
        internship_count=internship_count,
        service_count=service_count,
        featured_jobs=featured_jobs,
        featured_services=featured_services,
        recent_announcements=recent_announcements
    )

@app.route('/about')
def about():
    return render_template('about.html')

# -------------------------------------------------------------------
# DASHBOARD (ROLE-BASED ORCHESTRATION)
# -------------------------------------------------------------------

@app.route('/dashboard')
@login_required
def dashboard():
    user = g.user
    role = user['role']

    if role == 'student':
        # Student Dashboard Metrics
        profile = query_db("SELECT * FROM student_profiles WHERE user_id = ?", (user['id'],), one=True)
        analysis = calculate_profile_completion(user['id'])
        
        # Student skills list
        skills = query_db("SELECT * FROM skills WHERE student_id = ?", (user['id'],))
        
        # Applications
        applications = query_db("""
            SELECT a.*, 
                   COALESCE(j.title, i.title) as opp_title,
                   COALESCE(c_j.company_name, c_i.company_name) as company_name,
                   CASE WHEN a.job_id IS NOT NULL THEN 'Job' ELSE 'Internship' END as type
            FROM applications a
            LEFT JOIN jobs j ON a.job_id = j.id
            LEFT JOIN companies c_j ON j.company_id = c_j.id
            LEFT JOIN internships i ON a.internship_id = i.id
            LEFT JOIN companies c_i ON i.company_id = c_i.id
            WHERE a.user_id = ?
            ORDER BY a.id DESC LIMIT 5
        """, (user['id'],))

        # Services & Orders
        my_services = query_db("SELECT * FROM services WHERE provider_id = ?", (user['id'],))
        my_orders = query_db("""
            SELECT o.*, s.title as service_title, u.name as customer_name
            FROM orders o
            JOIN services s ON o.service_id = s.id
            JOIN users u ON o.customer_id = u.id
            WHERE o.provider_id = ?
            ORDER BY o.id DESC LIMIT 5
        """, (user['id'],))
        
        # Earnings calculation
        earnings_sum = query_db("SELECT COALESCE(SUM(amount), 0) as total FROM earnings WHERE provider_id = ?", (user['id'],), one=True)['total']
        pending_orders_count = query_db("SELECT COUNT(*) as cnt FROM orders WHERE provider_id = ? AND status IN ('Requested', 'Accepted', 'In Progress')", (user['id'],), one=True)['cnt']
        completed_orders_count = query_db("SELECT COUNT(*) as cnt FROM orders WHERE provider_id = ? AND status = 'Completed'", (user['id'],), one=True)['cnt']

        # Recent opportunities
        recent_opps = query_db("SELECT * FROM opportunities ORDER BY id DESC LIMIT 3")

        return render_template('dashboard.html',
            role=role,
            profile=profile,
            analysis=analysis,
            skills=skills,
            applications=applications,
            my_services=my_services,
            my_orders=my_orders,
            demo_earnings=earnings_sum,
            pending_orders_count=pending_orders_count,
            completed_orders_count=completed_orders_count,
            recent_opps=recent_opps
        )

    elif role == 'employer':
        # Employer Dashboard
        company = query_db("SELECT * FROM companies WHERE user_id = ?", (user['id'],), one=True)
        if not company:
            execute_db("INSERT INTO companies (user_id, company_name, location) VALUES (?, ?, ?)",
                       (user['id'], f"{user['name']}'s Company", "Tirupati"))
            company = query_db("SELECT * FROM companies WHERE user_id = ?", (user['id'],), one=True)

        my_jobs = query_db("SELECT * FROM jobs WHERE company_id = ? ORDER BY id DESC", (company['id'],))
        my_internships = query_db("SELECT * FROM internships WHERE company_id = ? ORDER BY id DESC", (company['id'],))

        # Recent applicants
        applicants = query_db("""
            SELECT a.*, u.name as student_name, u.email as student_email, u.avatar,
                   COALESCE(j.title, i.title) as position_title,
                   sp.course, sp.year
            FROM applications a
            JOIN users u ON a.user_id = u.id
            LEFT JOIN student_profiles sp ON u.id = sp.user_id
            LEFT JOIN jobs j ON a.job_id = j.id
            LEFT JOIN internships i ON a.internship_id = i.id
            WHERE (j.company_id = ? OR i.company_id = ?)
            ORDER BY a.id DESC LIMIT 8
        """, (company['id'], company['id']))

        return render_template('dashboard.html',
            role=role,
            company=company,
            my_jobs=my_jobs,
            my_internships=my_internships,
            applicants=applicants
        )

    elif role == 'customer':
        # Customer Dashboard
        my_orders = query_db("""
            SELECT o.*, s.title as service_title, u.name as provider_name,
                   r.rating, r.review
            FROM orders o
            JOIN services s ON o.service_id = s.id
            JOIN users u ON o.provider_id = u.id
            LEFT JOIN ratings r ON o.id = r.order_id
            WHERE o.customer_id = ?
            ORDER BY o.id DESC
        """, (user['id'],))

        popular_services = query_db("""
            SELECT s.*, u.name as provider_name,
                   COALESCE((SELECT AVG(rating) FROM ratings WHERE provider_id = s.provider_id), 5.0) as avg_rating
            FROM services s
            JOIN users u ON s.provider_id = u.id
            WHERE s.availability = 'Available'
            ORDER BY s.id DESC LIMIT 4
        """)

        return render_template('dashboard.html',
            role=role,
            my_orders=my_orders,
            popular_services=popular_services
        )

    elif role == 'admin':
        return redirect(url_for('admin'))

    return render_template('dashboard.html', role='unknown')

# -------------------------------------------------------------------
# STUDENT PROFILE & SKILLS MANAGEMENT
# -------------------------------------------------------------------

@app.route('/profile')
@login_required
def my_profile():
    return redirect(url_for('view_profile', user_id=g.user['id']))

@app.route('/profile/<int:user_id>')
def view_profile(user_id):
    target_user = query_db("SELECT id, name, email, role, phone, avatar, created_at FROM users WHERE id = ?", (user_id,), one=True)
    if not target_user:
        flash("User profile not found.", "warning")
        return redirect(url_for('index'))

    profile = query_db("SELECT * FROM student_profiles WHERE user_id = ?", (user_id,), one=True)
    skills = query_db("SELECT * FROM skills WHERE student_id = ? ORDER BY category, name", (user_id,))
    projects = query_db("SELECT * FROM projects WHERE student_id = ? ORDER BY id DESC", (user_id,))
    achievements = query_db("SELECT * FROM achievements WHERE student_id = ? ORDER BY id DESC", (user_id,))
    services = query_db("SELECT * FROM services WHERE provider_id = ? ORDER BY id DESC", (user_id,))
    
    # Rating stats
    avg_rating_row = query_db("SELECT AVG(rating) as avg, COUNT(*) as cnt FROM ratings WHERE provider_id = ?", (user_id,), one=True)
    avg_rating = round(avg_rating_row['avg'], 1) if avg_rating_row and avg_rating_row['avg'] else 5.0
    review_count = avg_rating_row['cnt'] if avg_rating_row else 0
    reviews = query_db("""
        SELECT r.*, u.name as customer_name, s.title as service_title
        FROM ratings r
        JOIN users u ON r.customer_id = u.id
        JOIN services s ON r.service_id = s.id
        WHERE r.provider_id = ?
        ORDER BY r.id DESC LIMIT 5
    """, (user_id,))

    # Check connection status if logged in
    is_connected = False
    if g.user and g.user['id'] != user_id:
        conn_check = query_db(
            "SELECT id FROM connections WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)",
            (g.user['id'], user_id, user_id, g.user['id']),
            one=True
        )
        is_connected = bool(conn_check)

    analysis = calculate_profile_completion(user_id)

    return render_template('profile.html',
        target_user=target_user,
        profile=profile,
        skills=skills,
        projects=projects,
        achievements=achievements,
        services=services,
        avg_rating=avg_rating,
        review_count=review_count,
        reviews=reviews,
        is_connected=is_connected,
        analysis=analysis
    )

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = g.user
    profile = query_db("SELECT * FROM student_profiles WHERE user_id = ?", (user['id'],), one=True)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        college = request.form.get('college', '').strip()
        department = request.form.get('department', '').strip()
        course = request.form.get('course', '').strip()
        year = request.form.get('year', '').strip()
        education = request.form.get('education', '').strip()
        cgpa = request.form.get('cgpa', None)
        bio = request.form.get('bio', '').strip()
        resume = request.form.get('resume', '').strip()
        preferred_job_type = request.form.get('preferred_job_type', '').strip()
        preferred_location = request.form.get('preferred_location', '').strip()

        try:
            cgpa_val = float(cgpa) if cgpa and cgpa.strip() else None
        except ValueError:
            cgpa_val = None

        # Update users table
        execute_db("UPDATE users SET name = ?, phone = ? WHERE id = ?", (name, phone, user['id']))

        # Update or insert student_profiles
        if profile:
            execute_db("""
                UPDATE student_profiles SET 
                    college = ?, department = ?, course = ?, year = ?,
                    education = ?, cgpa = ?, bio = ?, resume = ?,
                    preferred_job_type = ?, preferred_location = ?
                WHERE user_id = ?
            """, (college, department, course, year, education, cgpa_val, bio, resume, preferred_job_type, preferred_location, user['id']))
        else:
            execute_db("""
                INSERT INTO student_profiles (user_id, college, department, course, year, education, cgpa, bio, resume, preferred_job_type, preferred_location)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user['id'], college, department, course, year, education, cgpa_val, bio, resume, preferred_job_type, preferred_location))

        flash("Your profile portfolio has been successfully updated!", "success")
        return redirect(url_for('my_profile'))

    return render_template('edit_profile.html', profile=profile)

# -------------------------------------------------------------------
# MY SKILLS & DEDICATED SKILLS MANAGEMENT
# -------------------------------------------------------------------

@app.route('/skills')
@login_required
def skills():
    user_skills = query_db("SELECT * FROM skills WHERE student_id = ? ORDER BY category, name", (g.user['id'],))
    tech_skills = [s for s in user_skills if s['category'] == 'Technical']
    digital_skills = [s for s in user_skills if s['category'] == 'Digital']
    soft_skills = [s for s in user_skills if s['category'] == 'Soft']

    return render_template('skills.html',
        tech_skills=tech_skills,
        digital_skills=digital_skills,
        soft_skills=soft_skills,
        total_skills=len(user_skills)
    )

@app.route('/skills/add', methods=['POST'])
@login_required
def add_skill():
    name = request.form.get('name', '').strip()
    category = request.form.get('category', 'Technical').strip()
    level = request.form.get('level', 'Intermediate').strip()

    if not name:
        flash("Skill name cannot be empty.", "warning")
        return redirect(url_for('skills'))

    if category not in ['Technical', 'Digital', 'Soft']:
        category = 'Technical'
    if level not in ['Beginner', 'Intermediate', 'Advanced']:
        level = 'Intermediate'

    # Check if duplicate
    existing = query_db("SELECT id FROM skills WHERE student_id = ? AND LOWER(name) = ?", (g.user['id'], name.lower()), one=True)
    if existing:
        flash(f"Skill '{name}' is already in your profile.", "info")
    else:
        execute_db("INSERT INTO skills (student_id, name, category, level) VALUES (?, ?, ?, ?)",
                   (g.user['id'], name, category, level))
        flash(f"Skill '{name}' ({level}) added to {category} Skills!", "success")

    return redirect(url_for('skills'))

@app.route('/skills/delete/<int:skill_id>', methods=['POST'])
@login_required
def delete_skill(skill_id):
    skill = query_db("SELECT * FROM skills WHERE id = ? AND student_id = ?", (skill_id, g.user['id']), one=True)
    if skill:
        execute_db("DELETE FROM skills WHERE id = ?", (skill_id,))
        flash(f"Skill '{skill['name']}' removed.", "info")
    else:
        flash("Skill not found or unauthorized.", "danger")
    return redirect(url_for('skills'))

@app.route('/skills/edit/<int:skill_id>', methods=['POST'])
@login_required
def edit_skill(skill_id):
    level = request.form.get('level', 'Intermediate').strip()
    category = request.form.get('category', 'Technical').strip()
    if level in ['Beginner', 'Intermediate', 'Advanced'] and category in ['Technical', 'Digital', 'Soft']:
        execute_db("UPDATE skills SET level = ?, category = ? WHERE id = ? AND student_id = ?",
                   (level, category, skill_id, g.user['id']))
        flash("Skill updated successfully.", "success")
    return redirect(url_for('skills'))

# -------------------------------------------------------------------
# MY SKILLS ANALYSIS (NO AI)
# -------------------------------------------------------------------

@app.route('/skill-analysis')
@login_required
def skill_analysis():
    user_id = g.user['id']
    analysis = calculate_profile_completion(user_id)
    skills = query_db("SELECT * FROM skills WHERE student_id = ? ORDER BY category, name", (user_id,))

    # Level Percentage Mapping as specified in prompt:
    # Beginner = 40%, Intermediate = 70%, Advanced = 90%
    level_map = {
        'Beginner': 40,
        'Intermediate': 70,
        'Advanced': 90
    }

    skills_with_pct = []
    for s in skills:
        skills_with_pct.append({
            'id': s['id'],
            'name': s['name'],
            'category': s['category'],
            'level': s['level'],
            'percentage': level_map.get(s['level'], 70)
        })

    # Counts by category
    tech_count = len([s for s in skills if s['category'] == 'Technical'])
    digital_count = len([s for s in skills if s['category'] == 'Digital'])
    soft_count = len([s for s in skills if s['category'] == 'Soft'])

    # Related assets counts
    cert_count = query_db("SELECT COUNT(*) as cnt FROM achievements WHERE student_id = ? AND category = 'Certificate'", (user_id,), one=True)['cnt']
    ach_count = query_db("SELECT COUNT(*) as cnt FROM achievements WHERE student_id = ?", (user_id,), one=True)['cnt']
    proj_count = query_db("SELECT COUNT(*) as cnt FROM projects WHERE student_id = ?", (user_id,), one=True)['cnt']
    service_count = query_db("SELECT COUNT(*) as cnt FROM services WHERE provider_id = ?", (user_id,), one=True)['cnt']
    internship_app_count = query_db("SELECT COUNT(*) as cnt FROM applications WHERE user_id = ? AND internship_id IS NOT NULL", (user_id,), one=True)['cnt']

    return render_template('skill_analysis.html',
        analysis=analysis,
        skills=skills_with_pct,
        total_skills=len(skills),
        tech_count=tech_count,
        digital_count=digital_count,
        soft_count=soft_count,
        cert_count=cert_count,
        ach_count=ach_count,
        proj_count=proj_count,
        service_count=service_count,
        internship_app_count=internship_app_count
    )

# -------------------------------------------------------------------
# JOB PORTAL
# -------------------------------------------------------------------

@app.route('/jobs')
def jobs():
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    location = request.args.get('location', '').strip()
    job_type = request.args.get('job_type', '').strip()

    sql = """
        SELECT j.*, c.company_name, c.logo, c.location as company_location
        FROM jobs j
        JOIN companies c ON j.company_id = c.id
        WHERE 1=1
    """
    params = []

    if query:
        sql += " AND (j.title LIKE ? OR j.skills LIKE ? OR j.description LIKE ? OR c.company_name LIKE ?)"
        wildcard = f"%{query}%"
        params.extend([wildcard, wildcard, wildcard, wildcard])

    if category:
        sql += " AND j.category = ?"
        params.append(category)

    if location:
        sql += " AND (j.location LIKE ? OR c.location LIKE ?)"
        params.extend([f"%{location}%", f"%{location}%"])

    if job_type:
        sql += " AND j.job_type = ?"
        params.append(job_type)

    sql += " ORDER BY j.id DESC"
    all_jobs = query_db(sql, params)

    # Categories for filter
    categories = query_db("SELECT DISTINCT category FROM jobs ORDER BY category")

    # If user is student, compute Skill Compatibility for each job card
    student_skills_names = []
    if g.user and g.user['role'] == 'student':
        s_rows = query_db("SELECT name FROM skills WHERE student_id = ?", (g.user['id'],))
        student_skills_names = [r['name'] for r in s_rows]

    processed_jobs = []
    for job in all_jobs:
        job_dict = dict(job)
        if student_skills_names:
            compat = analyze_skill_compatibility(student_skills_names, job['skills'])
            job_dict['compat_score'] = compat['percentage']
        else:
            job_dict['compat_score'] = None
        processed_jobs.append(job_dict)

    return render_template('jobs.html',
        jobs=processed_jobs,
        categories=categories,
        search_query=query,
        selected_category=category,
        selected_location=location,
        selected_job_type=job_type
    )

@app.route('/jobs/<int:job_id>')
def job_details(job_id):
    job = query_db("""
        SELECT j.*, c.company_name, c.description as company_desc, c.location as company_location, c.website, c.logo, c.user_id as employer_id
        FROM jobs j
        JOIN companies c ON j.company_id = c.id
        WHERE j.id = ?
    """, (job_id,), one=True)

    if not job:
        flash("Job posting not found.", "warning")
        return redirect(url_for('jobs'))

    # Check if current user already applied
    already_applied = False
    application = None
    skill_compat = None

    if g.user:
        application = query_db("SELECT * FROM applications WHERE user_id = ? AND job_id = ?", (g.user['id'], job_id), one=True)
        already_applied = bool(application)

        if g.user['role'] == 'student':
            student_skills = query_db("SELECT name FROM skills WHERE student_id = ?", (g.user['id'],))
            s_list = [s['name'] for s in student_skills]
            # Transparent Python compatibility analysis - NO AI
            skill_compat = analyze_skill_compatibility(s_list, job['skills'])

    return render_template('job_details.html',
        job=job,
        already_applied=already_applied,
        application=application,
        skill_compat=skill_compat
    )

@app.route('/jobs/<int:job_id>/apply', methods=['POST'])
@login_required
@role_required('student')
def apply_job(job_id):
    cover_note = request.form.get('cover_note', '').strip()

    # Check existing application
    existing = query_db("SELECT id FROM applications WHERE user_id = ? AND job_id = ?", (g.user['id'], job_id), one=True)
    if existing:
        flash("You have already applied for this position.", "info")
        return redirect(url_for('job_details', job_id=job_id))

    execute_db(
        "INSERT INTO applications (user_id, job_id, cover_note, status) VALUES (?, ?, ?, 'Applied')",
        (g.user['id'], job_id, cover_note)
    )

    flash("🎉 Application submitted successfully! You can track its status in 'My Applications'.", "success")
    return redirect(url_for('my_applications'))

@app.route('/jobs/create', methods=['GET', 'POST'])
@login_required
@role_required('employer')
def create_job():
    company = query_db("SELECT * FROM companies WHERE user_id = ?", (g.user['id'],), one=True)
    if not company:
        flash("Please complete your company profile first.", "warning")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', 'Software & IT').strip()
        description = request.form.get('description', '').strip()
        responsibilities = request.form.get('responsibilities', '').strip()
        qualification = request.form.get('qualification', '').strip()
        skills = request.form.get('skills', '').strip()
        location = request.form.get('location', '').strip()
        job_type = request.form.get('job_type', 'Full-time').strip()
        salary = request.form.get('salary', '').strip()

        if not title or not description or not skills or not location or not salary:
            flash("Please fill in all mandatory job fields.", "danger")
            return render_template('create_job.html')

        execute_db("""
            INSERT INTO jobs (company_id, title, category, description, responsibilities, qualification, skills, location, job_type, salary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (company['id'], title, category, description, responsibilities, qualification, skills, location, job_type, salary))

        flash(f"Job posting '{title}' published successfully!", "success")
        return redirect(url_for('dashboard'))

    return render_template('create_job.html')

@app.route('/jobs/<int:job_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('employer')
def edit_job(job_id):
    job = query_db("""
        SELECT j.* FROM jobs j 
        JOIN companies c ON j.company_id = c.id 
        WHERE j.id = ? AND (c.user_id = ? OR ? = 'admin')
    """, (job_id, g.user['id'], g.user['role']), one=True)

    if not job:
        flash("Job not found or permission denied.", "danger")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        responsibilities = request.form.get('responsibilities', '').strip()
        qualification = request.form.get('qualification', '').strip()
        skills = request.form.get('skills', '').strip()
        location = request.form.get('location', '').strip()
        job_type = request.form.get('job_type', '').strip()
        salary = request.form.get('salary', '').strip()

        execute_db("""
            UPDATE jobs SET title = ?, category = ?, description = ?, responsibilities = ?, qualification = ?, skills = ?, location = ?, job_type = ?, salary = ?
            WHERE id = ?
        """, (title, category, description, responsibilities, qualification, skills, location, job_type, salary, job_id))

        flash("Job posting updated successfully.", "success")
        return redirect(url_for('job_details', job_id=job_id))

    return render_template('edit_job.html', job=job)

@app.route('/jobs/<int:job_id>/delete', methods=['POST'])
@login_required
@role_required('employer')
def delete_job(job_id):
    job = query_db("""
        SELECT j.* FROM jobs j 
        JOIN companies c ON j.company_id = c.id 
        WHERE j.id = ? AND (c.user_id = ? OR ? = 'admin')
    """, (job_id, g.user['id'], g.user['role']), one=True)

    if job:
        execute_db("DELETE FROM jobs WHERE id = ?", (job_id,))
        flash("Job posting removed.", "info")
    else:
        flash("Permission denied.", "danger")
    return redirect(url_for('dashboard'))

# -------------------------------------------------------------------
# INTERNSHIP PORTAL
# -------------------------------------------------------------------

@app.route('/internships')
def internships():
    query = request.args.get('q', '').strip()
    duration = request.args.get('duration', '').strip()
    location = request.args.get('location', '').strip()

    sql = """
        SELECT i.*, c.company_name, c.logo, c.location as company_location
        FROM internships i
        JOIN companies c ON i.company_id = c.id
        WHERE 1=1
    """
    params = []

    if query:
        sql += " AND (i.title LIKE ? OR i.skills LIKE ? OR i.description LIKE ? OR c.company_name LIKE ?)"
        wildcard = f"%{query}%"
        params.extend([wildcard, wildcard, wildcard, wildcard])

    if duration:
        sql += " AND i.duration LIKE ?"
        params.append(f"%{duration}%")

    if location:
        sql += " AND (i.location LIKE ? OR c.location LIKE ?)"
        params.extend([f"%{location}%", f"%{location}%"])

    sql += " ORDER BY i.id DESC"
    all_internships = query_db(sql, params)

    # Student skills
    student_skills_names = []
    if g.user and g.user['role'] == 'student':
        s_rows = query_db("SELECT name FROM skills WHERE student_id = ?", (g.user['id'],))
        student_skills_names = [r['name'] for r in s_rows]

    processed_internships = []
    for it in all_internships:
        it_dict = dict(it)
        if student_skills_names:
            compat = analyze_skill_compatibility(student_skills_names, it['skills'])
            it_dict['compat_score'] = compat['percentage']
        else:
            it_dict['compat_score'] = None
        processed_internships.append(it_dict)

    return render_template('internships.html',
        internships=processed_internships,
        search_query=query,
        selected_duration=duration,
        selected_location=location
    )

@app.route('/internships/<int:internship_id>')
def internship_details(internship_id):
    internship = query_db("""
        SELECT i.*, c.company_name, c.description as company_desc, c.location as company_location, c.website, c.logo
        FROM internships i
        JOIN companies c ON i.company_id = c.id
        WHERE i.id = ?
    """, (internship_id,), one=True)

    if not internship:
        flash("Internship not found.", "warning")
        return redirect(url_for('internships'))

    already_applied = False
    application = None
    skill_compat = None

    if g.user:
        application = query_db("SELECT * FROM applications WHERE user_id = ? AND internship_id = ?", (g.user['id'], internship_id), one=True)
        already_applied = bool(application)

        if g.user['role'] == 'student':
            student_skills = query_db("SELECT name FROM skills WHERE student_id = ?", (g.user['id'],))
            s_list = [s['name'] for s in student_skills]
            skill_compat = analyze_skill_compatibility(s_list, internship['skills'])

    return render_template('internship_details.html',
        internship=internship,
        already_applied=already_applied,
        application=application,
        skill_compat=skill_compat
    )

@app.route('/internships/<int:internship_id>/apply', methods=['POST'])
@login_required
@role_required('student')
def apply_internship(internship_id):
    cover_note = request.form.get('cover_note', '').strip()

    existing = query_db("SELECT id FROM applications WHERE user_id = ? AND internship_id = ?", (g.user['id'], internship_id), one=True)
    if existing:
        flash("You have already applied for this internship.", "info")
        return redirect(url_for('internship_details', internship_id=internship_id))

    execute_db(
        "INSERT INTO applications (user_id, internship_id, cover_note, status) VALUES (?, ?, ?, 'Applied')",
        (g.user['id'], internship_id, cover_note)
    )

    flash("🎉 Internship application submitted successfully!", "success")
    return redirect(url_for('my_applications'))

@app.route('/internships/create', methods=['GET', 'POST'])
@login_required
@role_required('employer')
def create_internship():
    company = query_db("SELECT * FROM companies WHERE user_id = ?", (g.user['id'],), one=True)
    if not company:
        flash("Please complete your company profile first.", "warning")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        skills = request.form.get('skills', '').strip()
        eligibility = request.form.get('eligibility', '').strip()
        duration = request.form.get('duration', '').strip()
        stipend = request.form.get('stipend', '').strip()
        location = request.form.get('location', '').strip()
        deadline = request.form.get('deadline', '').strip()

        execute_db("""
            INSERT INTO internships (company_id, title, description, skills, eligibility, duration, stipend, location, deadline)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (company['id'], title, description, skills, eligibility, duration, stipend, location, deadline))

        flash(f"Internship '{title}' posted successfully!", "success")
        return redirect(url_for('dashboard'))

    return render_template('create_internship.html')

# -------------------------------------------------------------------
# APPLICATIONS MANAGEMENT
# -------------------------------------------------------------------

@app.route('/applications')
@login_required
def my_applications():
    user = g.user
    if user['role'] == 'student':
        # Applications submitted by student
        apps = query_db("""
            SELECT a.*, 
                   COALESCE(j.title, i.title) as title,
                   COALESCE(c_j.company_name, c_i.company_name) as company_name,
                   COALESCE(j.location, i.location) as location,
                   CASE WHEN a.job_id IS NOT NULL THEN 'Job' ELSE 'Internship' END as opp_type,
                   a.job_id, a.internship_id
            FROM applications a
            LEFT JOIN jobs j ON a.job_id = j.id
            LEFT JOIN companies c_j ON j.company_id = c_j.id
            LEFT JOIN internships i ON a.internship_id = i.id
            LEFT JOIN companies c_i ON i.company_id = c_i.id
            WHERE a.user_id = ?
            ORDER BY a.id DESC
        """, (user['id'],))
        return render_template('applications.html', applications=apps, is_employer=False)

    elif user['role'] in ['employer', 'admin']:
        # Applications received by employer
        company = query_db("SELECT id FROM companies WHERE user_id = ?", (user['id'],), one=True)
        company_id = company['id'] if company else 0

        apps = query_db("""
            SELECT a.*, u.name as student_name, u.email as student_email, u.phone as student_phone, u.avatar,
                   COALESCE(j.title, i.title) as title,
                   COALESCE(j.skills, i.skills) as req_skills,
                   CASE WHEN a.job_id IS NOT NULL THEN 'Job' ELSE 'Internship' END as opp_type,
                   sp.course, sp.year, sp.cgpa
            FROM applications a
            JOIN users u ON a.user_id = u.id
            LEFT JOIN student_profiles sp ON u.id = sp.user_id
            LEFT JOIN jobs j ON a.job_id = j.id
            LEFT JOIN internships i ON a.internship_id = i.id
            WHERE (j.company_id = ? OR i.company_id = ? OR ? = 'admin')
            ORDER BY a.id DESC
        """, (company_id, company_id, user['role']))

        # Calculate skill compatibility for each applicant
        processed_apps = []
        for app_item in apps:
            app_dict = dict(app_item)
            student_skills = query_db("SELECT name FROM skills WHERE student_id = ?", (app_item['user_id'],))
            s_list = [s['name'] for s in student_skills]
            compat = analyze_skill_compatibility(s_list, app_item['req_skills'])
            app_dict['compat_score'] = compat['percentage']
            app_dict['matched_skills'] = compat['matched']
            app_dict['missing_skills'] = compat['missing']
            processed_apps.append(app_dict)

        return render_template('applications.html', applications=processed_apps, is_employer=True)

    else:
        flash("You do not have access to applications.", "warning")
        return redirect(url_for('dashboard'))

@app.route('/applications/update-status/<int:app_id>', methods=['POST'])
@login_required
@role_required('employer', 'admin')
def update_application_status(app_id):
    new_status = request.form.get('status', '').strip()
    if new_status in ['Applied', 'Under Review', 'Shortlisted', 'Selected', 'Rejected']:
        execute_db(
            "UPDATE applications SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_status, app_id)
        )
        flash(f"Application status successfully updated to '{new_status}'.", "success")
    else:
        flash("Invalid status value.", "danger")
    return redirect(url_for('my_applications'))

# -------------------------------------------------------------------
# SKILL-TO-EARN MARKETPLACE
# -------------------------------------------------------------------

@app.route('/services')
def services():
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    max_price = request.args.get('max_price', '').strip()

    sql = """
        SELECT s.*, u.name as provider_name, u.avatar,
               COALESCE((SELECT AVG(rating) FROM ratings WHERE provider_id = s.provider_id), 5.0) as avg_rating,
               (SELECT COUNT(*) FROM ratings WHERE provider_id = s.provider_id) as review_count,
               sp.course, sp.year
        FROM services s
        JOIN users u ON s.provider_id = u.id
        LEFT JOIN student_profiles sp ON u.id = sp.user_id
        WHERE 1=1
    """
    params = []

    if query:
        sql += " AND (s.title LIKE ? OR s.skills LIKE ? OR s.description LIKE ? OR u.name LIKE ?)"
        wildcard = f"%{query}%"
        params.extend([wildcard, wildcard, wildcard, wildcard])

    if category:
        sql += " AND s.category = ?"
        params.append(category)

    if max_price:
        try:
            sql += " AND s.price <= ?"
            params.append(float(max_price))
        except ValueError:
            pass

    sql += " ORDER BY s.id DESC"
    marketplace_services = query_db(sql, params)

    categories = query_db("SELECT DISTINCT category FROM services ORDER BY category")

    return render_template('services.html',
        services=marketplace_services,
        categories=categories,
        search_query=query,
        selected_category=category,
        max_price=max_price
    )

@app.route('/services/<int:service_id>')
def service_details(service_id):
    service = query_db("""
        SELECT s.*, u.name as provider_name, u.email as provider_email, u.phone as provider_phone, u.avatar,
               sp.course, sp.year, sp.bio,
               COALESCE((SELECT AVG(rating) FROM ratings WHERE provider_id = s.provider_id), 5.0) as avg_rating,
               (SELECT COUNT(*) FROM ratings WHERE provider_id = s.provider_id) as review_count
        FROM services s
        JOIN users u ON s.provider_id = u.id
        LEFT JOIN student_profiles sp ON u.id = sp.user_id
        WHERE s.id = ?
    """, (service_id,), one=True)

    if not service:
        flash("Service not found.", "warning")
        return redirect(url_for('services'))

    reviews = query_db("""
        SELECT r.*, u.name as customer_name, u.avatar as customer_avatar
        FROM ratings r
        JOIN users u ON r.customer_id = u.id
        WHERE r.service_id = ?
        ORDER BY r.id DESC
    """, (service_id,))

    return render_template('service_details.html', service=service, reviews=reviews)

@app.route('/services/create', methods=['GET', 'POST'])
@login_required
@role_required('student')
def create_service():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', 'Academic & Writing').strip()
        description = request.form.get('description', '').strip()
        skills = request.form.get('skills', '').strip()
        price = request.form.get('price', '').strip()
        delivery_time = request.form.get('delivery_time', '2 Days').strip()
        availability = request.form.get('availability', 'Available').strip()

        if not title or not description or not price:
            flash("Please fill in the title, description, and price.", "danger")
            return render_template('create_service.html')

        try:
            price_val = float(price)
        except ValueError:
            flash("Please enter a valid numeric price.", "danger")
            return render_template('create_service.html')

        execute_db("""
            INSERT INTO services (provider_id, title, category, description, skills, price, delivery_time, availability)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (g.user['id'], title, category, description, skills, price_val, delivery_time, availability))

        flash(f"✨ Service '{title}' listed successfully in the Skill Marketplace!", "success")
        return redirect(url_for('services'))

    return render_template('create_service.html')

@app.route('/services/<int:service_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('student')
def edit_service(service_id):
    service = query_db("SELECT * FROM services WHERE id = ? AND provider_id = ?", (service_id, g.user['id']), one=True)
    if not service:
        flash("Service not found or permission denied.", "danger")
        return redirect(url_for('services'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        skills = request.form.get('skills', '').strip()
        price = request.form.get('price', '').strip()
        delivery_time = request.form.get('delivery_time', '').strip()
        availability = request.form.get('availability', 'Available').strip()

        try:
            price_val = float(price)
            execute_db("""
                UPDATE services SET title = ?, category = ?, description = ?, skills = ?, price = ?, delivery_time = ?, availability = ?
                WHERE id = ?
            """, (title, category, description, skills, price_val, delivery_time, availability, service_id))
            flash("Service listing updated successfully.", "success")
            return redirect(url_for('service_details', service_id=service_id))
        except ValueError:
            flash("Invalid price value.", "danger")

    return render_template('edit_service.html', service=service)

@app.route('/services/<int:service_id>/delete', methods=['POST'])
@login_required
@role_required('student')
def delete_service(service_id):
    service = query_db("SELECT * FROM services WHERE id = ? AND (provider_id = ? OR ? = 'admin')",
                       (service_id, g.user['id'], g.user['role']), one=True)
    if service:
        execute_db("DELETE FROM services WHERE id = ?", (service_id,))
        flash("Service removed from marketplace.", "info")
    else:
        flash("Permission denied.", "danger")
    return redirect(url_for('dashboard'))

# -------------------------------------------------------------------
# ORDER SYSTEM, DEMO EARNINGS & RATINGS
# -------------------------------------------------------------------

@app.route('/services/<int:service_id>/order', methods=['POST'])
@login_required
def place_order(service_id):
    service = query_db("SELECT * FROM services WHERE id = ?", (service_id,), one=True)
    if not service:
        flash("Service does not exist.", "danger")
        return redirect(url_for('services'))

    if service['provider_id'] == g.user['id']:
        flash("You cannot order your own service!", "warning")
        return redirect(url_for('service_details', service_id=service_id))

    requirements = request.form.get('requirements', '').strip()
    if not requirements:
        flash("Please describe your requirements for this service.", "warning")
        return redirect(url_for('service_details', service_id=service_id))

    order_id = execute_db("""
        INSERT INTO orders (service_id, customer_id, provider_id, requirements, status, amount)
        VALUES (?, ?, ?, ?, 'Requested', ?)
    """, (service_id, g.user['id'], service['provider_id'], requirements, service['price']))

    flash(f"🎉 Service requested! Order #{order_id} has been submitted to the provider.", "success")
    return redirect(url_for('orders'))

@app.route('/orders')
@login_required
def orders():
    user = g.user
    if user['role'] == 'student':
        # Orders received as provider
        incoming_orders = query_db("""
            SELECT o.*, s.title as service_title, u.name as customer_name, u.phone as customer_phone,
                   r.rating, r.review
            FROM orders o
            JOIN services s ON o.service_id = s.id
            JOIN users u ON o.customer_id = u.id
            LEFT JOIN ratings r ON o.id = r.order_id
            WHERE o.provider_id = ?
            ORDER BY o.id DESC
        """, (user['id'],))
        return render_template('orders.html', orders=incoming_orders, is_provider=True)

    else:
        # Orders placed as customer / employer / admin
        my_orders = query_db("""
            SELECT o.*, s.title as service_title, u.name as provider_name, u.phone as provider_phone,
                   r.rating, r.review
            FROM orders o
            JOIN services s ON o.service_id = s.id
            JOIN users u ON o.provider_id = u.id
            LEFT JOIN ratings r ON o.id = r.order_id
            WHERE o.customer_id = ? OR ? = 'admin'
            ORDER BY o.id DESC
        """, (user['id'], user['role']))
        return render_template('orders.html', orders=my_orders, is_provider=False)

@app.route('/orders/<int:order_id>/status', methods=['POST'])
@login_required
def update_order_status(order_id):
    order = query_db("SELECT * FROM orders WHERE id = ?", (order_id,), one=True)
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for('orders'))

    # Only provider or admin can transition status
    if order['provider_id'] != g.user['id'] and g.user['role'] != 'admin':
        flash("Permission denied.", "danger")
        return redirect(url_for('orders'))

    new_status = request.form.get('status', '').strip()
    if new_status in ['Accepted', 'In Progress', 'Completed', 'Cancelled']:
        completed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if new_status == 'Completed' else None
        
        execute_db("""
            UPDATE orders SET status = ?, completed_at = COALESCE(?, completed_at)
            WHERE id = ?
        """, (new_status, completed_at, order_id))

        # If order completed, automatically record in earnings!
        if new_status == 'Completed':
            existing_earning = query_db("SELECT id FROM earnings WHERE order_id = ?", (order_id,), one=True)
            if not existing_earning:
                execute_db("""
                    INSERT INTO earnings (provider_id, order_id, amount, date)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (order['provider_id'], order_id, order['amount']))
                flash(f"🎉 Order #{order_id} marked as Completed! ₹{order['amount']:.0f} credited to your Demo Earnings.", "success")
        else:
            flash(f"Order #{order_id} status updated to '{new_status}'.", "info")

    return redirect(url_for('orders'))

@app.route('/orders/<int:order_id>/rate', methods=['POST'])
@login_required
def rate_order(order_id):
    order = query_db("SELECT * FROM orders WHERE id = ?", (order_id,), one=True)
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for('orders'))

    if order['customer_id'] != g.user['id'] and g.user['role'] != 'admin':
        flash("Only the customer who ordered this service can rate it.", "danger")
        return redirect(url_for('orders'))

    if order['status'] != 'Completed':
        flash("Only completed orders can be reviewed.", "warning")
        return redirect(url_for('orders'))

    rating = request.form.get('rating', '5')
    review = request.form.get('review', '').strip()

    try:
        rating_val = int(rating)
        if not (1 <= rating_val <= 5):
            rating_val = 5
    except ValueError:
        rating_val = 5

    # Check if already rated
    existing = query_db("SELECT id FROM ratings WHERE order_id = ?", (order_id,), one=True)
    if existing:
        execute_db("UPDATE ratings SET rating = ?, review = ? WHERE order_id = ?", (rating_val, review, order_id))
        flash("Your review has been updated!", "success")
    else:
        execute_db("""
            INSERT INTO ratings (order_id, customer_id, provider_id, service_id, rating, review)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (order_id, g.user['id'], order['provider_id'], order['service_id'], rating_val, review))
        flash(f"⭐ Thank you! Your {rating_val}-star rating and review have been recorded.", "success")

    return redirect(url_for('orders'))

@app.route('/earnings')
@login_required
@role_required('student')
def my_earnings():
    user_id = g.user['id']
    
    # Calculate earnings totals
    total_earnings_row = query_db("SELECT COALESCE(SUM(amount), 0) as total FROM earnings WHERE provider_id = ?", (user_id,), one=True)
    total_earnings = total_earnings_row['total'] if total_earnings_row else 0.0

    total_orders = query_db("SELECT COUNT(*) as cnt FROM orders WHERE provider_id = ?", (user_id,), one=True)['cnt']
    completed_orders = query_db("SELECT COUNT(*) as cnt FROM orders WHERE provider_id = ? AND status = 'Completed'", (user_id,), one=True)['cnt']
    pending_orders = query_db("SELECT COUNT(*) as cnt FROM orders WHERE provider_id = ? AND status IN ('Requested', 'Accepted', 'In Progress')", (user_id,), one=True)['cnt']

    # Transaction list
    earnings_history = query_db("""
        SELECT e.*, s.title as service_title, u.name as customer_name
        FROM earnings e
        JOIN orders o ON e.order_id = o.id
        JOIN services s ON o.service_id = s.id
        JOIN users u ON o.customer_id = u.id
        WHERE e.provider_id = ?
        ORDER BY e.id DESC
    """, (user_id,))

    return render_template('earnings.html',
        total_earnings=total_earnings,
        total_orders=total_orders,
        completed_orders=completed_orders,
        pending_orders=pending_orders,
        history=earnings_history
    )

# -------------------------------------------------------------------
# OPPORTUNITIES (HACKATHONS, IDEATHONS, COMPETITIONS)
# -------------------------------------------------------------------

@app.route('/opportunities')
def opportunities():
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()

    sql = "SELECT * FROM opportunities WHERE 1=1"
    params = []

    if query:
        sql += " AND (title LIKE ? OR description LIKE ? OR organization LIKE ?)"
        wildcard = f"%{query}%"
        params.extend([wildcard, wildcard, wildcard])

    if category:
        sql += " AND category = ?"
        params.append(category)

    sql += " ORDER BY id DESC"
    opps = query_db(sql, params)

    categories = query_db("SELECT DISTINCT category FROM opportunities ORDER BY category")

    return render_template('opportunities.html',
        opportunities=opps,
        categories=categories,
        search_query=query,
        selected_category=category
    )

@app.route('/opportunities/create', methods=['POST'])
@login_required
@role_required('admin')
def create_opportunity():
    title = request.form.get('title', '').strip()
    category = request.form.get('category', 'Ideathon').strip()
    organization = request.form.get('organization', '').strip()
    description = request.form.get('description', '').strip()
    date = request.form.get('date', '').strip()
    location = request.form.get('location', '').strip()
    deadline = request.form.get('deadline', '').strip()
    link = request.form.get('link', '').strip()

    execute_db("""
        INSERT INTO opportunities (title, category, organization, description, date, location, deadline, link)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (title, category, organization, description, date, location, deadline, link))

    flash(f"Opportunity '{title}' created successfully!", "success")
    return redirect(url_for('opportunities'))

@app.route('/opportunities/<int:opp_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_opportunity(opp_id):
    execute_db("DELETE FROM opportunities WHERE id = ?", (opp_id,))
    flash("Opportunity deleted.", "info")
    return redirect(url_for('opportunities'))

# -------------------------------------------------------------------
# STUDENT PROJECTS SHOWCASE
# -------------------------------------------------------------------

@app.route('/projects')
def projects():
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()

    sql = """
        SELECT p.*, u.name as student_name, u.avatar, sp.course, sp.year
        FROM projects p
        JOIN users u ON p.student_id = u.id
        LEFT JOIN student_profiles sp ON u.id = sp.user_id
        WHERE 1=1
    """
    params = []

    if query:
        sql += " AND (p.title LIKE ? OR p.technologies LIKE ? OR p.description LIKE ? OR u.name LIKE ?)"
        wildcard = f"%{query}%"
        params.extend([wildcard, wildcard, wildcard, wildcard])

    if category:
        sql += " AND p.category = ?"
        params.append(category)

    sql += " ORDER BY p.id DESC"
    all_projects = query_db(sql, params)

    categories = query_db("SELECT DISTINCT category FROM projects ORDER BY category")

    return render_template('projects.html',
        projects=all_projects,
        categories=categories,
        search_query=query,
        selected_category=category
    )

@app.route('/projects/add', methods=['GET', 'POST'])
@login_required
@role_required('student')
def add_project():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        technologies = request.form.get('technologies', '').strip()
        team_members = request.form.get('team_members', '').strip()
        category = request.form.get('category', 'Web & Software').strip()
        status = request.form.get('status', 'Completed').strip()
        project_link = request.form.get('project_link', '').strip()

        if not title or not description or not technologies:
            flash("Please fill in project title, description, and technologies.", "danger")
            return render_template('add_project.html')

        execute_db("""
            INSERT INTO projects (student_id, title, description, technologies, team_members, category, status, project_link)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (g.user['id'], title, description, technologies, team_members, category, status, project_link))

        flash(f"Project '{title}' added to your portfolio showcase!", "success")
        return redirect(url_for('projects'))

    return render_template('add_project.html')

@app.route('/projects/<int:proj_id>/delete', methods=['POST'])
@login_required
def delete_project(proj_id):
    proj = query_db("SELECT * FROM projects WHERE id = ? AND (student_id = ? OR ? = 'admin')",
                    (proj_id, g.user['id'], g.user['role']), one=True)
    if proj:
        execute_db("DELETE FROM projects WHERE id = ?", (proj_id,))
        flash("Project deleted.", "info")
    else:
        flash("Permission denied.", "danger")
    return redirect(url_for('projects'))

# -------------------------------------------------------------------
# ACHIEVEMENTS PORTAL
# -------------------------------------------------------------------

@app.route('/achievements')
def achievements():
    category = request.args.get('category', '').strip()
    sql = """
        SELECT a.*, u.name as student_name, u.avatar, sp.course, sp.year
        FROM achievements a
        JOIN users u ON a.student_id = u.id
        LEFT JOIN student_profiles sp ON u.id = sp.user_id
        WHERE 1=1
    """
    params = []

    if category:
        sql += " AND a.category = ?"
        params.append(category)

    sql += " ORDER BY a.id DESC"
    ach_list = query_db(sql, params)

    categories = query_db("SELECT DISTINCT category FROM achievements ORDER BY category")

    return render_template('achievements.html',
        achievements=ach_list,
        categories=categories,
        selected_category=category
    )

@app.route('/achievements/add', methods=['GET', 'POST'])
@login_required
@role_required('student')
def add_achievement():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', 'Award').strip()
        organization = request.form.get('organization', '').strip()
        description = request.form.get('description', '').strip()
        date = request.form.get('date', '').strip()
        proof_link = request.form.get('proof_link', '').strip()

        if not title or not organization:
            flash("Please enter achievement title and issuing organization.", "danger")
            return render_template('add_achievement.html')

        execute_db("""
            INSERT INTO achievements (student_id, title, category, organization, description, date, proof_link)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (g.user['id'], title, category, organization, description, date, proof_link))

        flash(f"Achievement '{title}' recorded!", "success")
        return redirect(url_for('achievements'))

    return render_template('add_achievement.html')

@app.route('/achievements/<int:ach_id>/delete', methods=['POST'])
@login_required
def delete_achievement(ach_id):
    ach = query_db("SELECT * FROM achievements WHERE id = ? AND (student_id = ? OR ? = 'admin')",
                   (ach_id, g.user['id'], g.user['role']), one=True)
    if ach:
        execute_db("DELETE FROM achievements WHERE id = ?", (ach_id,))
        flash("Achievement removed.", "info")
    else:
        flash("Permission denied.", "danger")
    return redirect(url_for('achievements'))

# -------------------------------------------------------------------
# CONNECT PORTAL (NETWORKING)
# -------------------------------------------------------------------

@app.route('/connections')
@login_required
def connections():
    user = g.user
    role_filter = request.args.get('role', '').strip()
    query = request.args.get('q', '').strip()

    sql = """
        SELECT u.id, u.name, u.email, u.role, u.avatar,
               sp.course, sp.year, sp.department,
               c.company_name,
               (SELECT COUNT(*) FROM connections WHERE (sender_id = ? AND receiver_id = u.id) OR (sender_id = u.id AND receiver_id = ?)) as is_connected
        FROM users u
        LEFT JOIN student_profiles sp ON u.id = sp.user_id
        LEFT JOIN companies c ON u.id = c.user_id
        WHERE u.id != ?
    """
    params = [user['id'], user['id'], user['id']]

    if role_filter:
        sql += " AND u.role = ?"
        params.append(role_filter)

    if query:
        sql += " AND (u.name LIKE ? OR sp.course LIKE ? OR c.company_name LIKE ?)"
        wildcard = f"%{query}%"
        params.extend([wildcard, wildcard, wildcard])

    sql += " ORDER BY is_connected DESC, u.name ASC"
    network_users = query_db(sql, params)

    connected_count = query_db(
        "SELECT COUNT(*) as cnt FROM connections WHERE sender_id = ? OR receiver_id = ?",
        (user['id'], user['id']), one=True
    )['cnt']

    return render_template('connections.html',
        users=network_users,
        connected_count=connected_count,
        selected_role=role_filter,
        search_query=query
    )

@app.route('/connections/toggle/<int:target_id>', methods=['POST'])
@login_required
def toggle_connection(target_id):
    if target_id == g.user['id']:
        flash("You cannot connect with yourself!", "warning")
        return redirect(url_for('connections'))

    existing = query_db(
        "SELECT id FROM connections WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)",
        (g.user['id'], target_id, target_id, g.user['id']),
        one=True
    )

    if existing:
        execute_db("DELETE FROM connections WHERE id = ?", (existing['id'],))
        flash("Connection removed.", "info")
    else:
        execute_db("INSERT INTO connections (sender_id, receiver_id) VALUES (?, ?)", (g.user['id'], target_id))
        target_name = query_db("SELECT name FROM users WHERE id = ?", (target_id,), one=True)['name']
        flash(f"🤝 You are now connected with {target_name}!", "success")

    return redirect(request.referrer or url_for('connections'))

# -------------------------------------------------------------------
# MRDU CAMPUS & ANNOUNCEMENTS
# -------------------------------------------------------------------

@app.route('/campus')
def campus():
    announcements = query_db("SELECT * FROM announcements ORDER BY id DESC LIMIT 5")
    recent_projects = query_db("""
        SELECT p.*, u.name as student_name 
        FROM projects p 
        JOIN users u ON p.student_id = u.id 
        ORDER BY p.id DESC LIMIT 4
    """)
    recent_achievements = query_db("""
        SELECT a.*, u.name as student_name 
        FROM achievements a 
        JOIN users u ON a.student_id = u.id 
        ORDER BY a.id DESC LIMIT 4
    """)
    opportunities = query_db("SELECT * FROM opportunities ORDER BY id DESC LIMIT 4")

    return render_template('campus.html',
        announcements=announcements,
        projects=recent_projects,
        achievements=recent_achievements,
        opportunities=opportunities
    )

@app.route('/announcements')
def announcements():
    all_announcements = query_db("SELECT * FROM announcements ORDER BY id DESC")
    return render_template('announcements.html', announcements=all_announcements)

@app.route('/announcements/create', methods=['POST'])
@login_required
@role_required('admin')
def create_announcement():
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    category = request.form.get('category', 'General').strip()
    date = datetime.now().strftime('%d %B %Y')

    if title and content:
        execute_db("INSERT INTO announcements (title, content, category, date) VALUES (?, ?, ?, ?)",
                   (title, content, category, date))
        flash("Campus announcement published!", "success")
    else:
        flash("Title and content are required.", "danger")
    return redirect(url_for('admin'))

@app.route('/announcements/<int:ann_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_announcement(ann_id):
    execute_db("DELETE FROM announcements WHERE id = ?", (ann_id,))
    flash("Announcement removed.", "info")
    return redirect(url_for('admin'))

# -------------------------------------------------------------------
# ADMIN DASHBOARD
# -------------------------------------------------------------------

@app.route('/admin')
@login_required
@role_required('admin')
def admin():
    # User counts
    total_users = query_db("SELECT COUNT(*) as cnt FROM users", one=True)['cnt']
    total_students = query_db("SELECT COUNT(*) as cnt FROM users WHERE role = 'student'", one=True)['cnt']
    total_employers = query_db("SELECT COUNT(*) as cnt FROM users WHERE role = 'employer'", one=True)['cnt']
    total_customers = query_db("SELECT COUNT(*) as cnt FROM users WHERE role = 'customer'", one=True)['cnt']

    # Opportunity counts
    total_jobs = query_db("SELECT COUNT(*) as cnt FROM jobs", one=True)['cnt']
    total_internships = query_db("SELECT COUNT(*) as cnt FROM internships", one=True)['cnt']
    total_services = query_db("SELECT COUNT(*) as cnt FROM services", one=True)['cnt']
    total_opportunities = query_db("SELECT COUNT(*) as cnt FROM opportunities", one=True)['cnt']

    # Activity counts
    total_apps = query_db("SELECT COUNT(*) as cnt FROM applications", one=True)['cnt']
    total_orders = query_db("SELECT COUNT(*) as cnt FROM orders", one=True)['cnt']
    completed_orders = query_db("SELECT COUNT(*) as cnt FROM orders WHERE status = 'Completed'", one=True)['cnt']
    total_ratings = query_db("SELECT COUNT(*) as cnt FROM ratings", one=True)['cnt']

    # Earnings
    total_demo_earnings = query_db("SELECT COALESCE(SUM(amount), 0) as total FROM earnings", one=True)['total']

    # Tables for moderation
    all_users = query_db("SELECT id, name, email, role, phone, created_at FROM users ORDER BY id DESC")
    all_jobs = query_db("SELECT j.*, c.company_name FROM jobs j JOIN companies c ON j.company_id = c.id ORDER BY j.id DESC")
    all_services = query_db("SELECT s.*, u.name as provider_name FROM services s JOIN users u ON s.provider_id = u.id ORDER BY s.id DESC")
    all_announcements = query_db("SELECT * FROM announcements ORDER BY id DESC")

    return render_template('admin.html',
        total_users=total_users,
        total_students=total_students,
        total_employers=total_employers,
        total_customers=total_customers,
        total_jobs=total_jobs,
        total_internships=total_internships,
        total_services=total_services,
        total_opportunities=total_opportunities,
        total_apps=total_apps,
        total_orders=total_orders,
        completed_orders=completed_orders,
        total_ratings=total_ratings,
        total_demo_earnings=total_demo_earnings,
        users=all_users,
        jobs=all_jobs,
        services=all_services,
        announcements=all_announcements
    )

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_user(user_id):
    if user_id == g.user['id']:
        flash("You cannot delete your own admin account.", "danger")
        return redirect(url_for('admin'))

    target = query_db("SELECT name FROM users WHERE id = ?", (user_id,), one=True)
    if target:
        execute_db("DELETE FROM users WHERE id = ?", (user_id,))
        flash(f"User '{target['name']}' and all associated records deleted.", "info")
    return redirect(url_for('admin'))

# -------------------------------------------------------------------
# ERROR HANDLERS
# -------------------------------------------------------------------

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# -------------------------------------------------------------------
# MAIN EXECUTION
# -------------------------------------------------------------------

if __name__ == '__main__':
    # Ensure database exists
    from database.db import DB_PATH, init_db
    if not os.path.exists(DB_PATH):
        init_db()
        from database.seed_data import seed_database
        seed_database()

    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    print("=" * 60)
    print("[STARTING] MR EARN & CONNECT - Server Starting")
    print("Malla Reddy Deemed to be University (MRDU), Tirupati")
    print("URL: http://127.0.0.1:5000")
    print("Demo Accounts:")
    print("  Student:  arjun@student.mrdu.edu    / Student@123")
    print("  Employer: techcorp@company.com      / Employer@123")
    print("  Customer: sharma@faculty.mrdu.edu   / Customer@123")
    print("  Admin:    admin@mrearn.mrdu.edu     / Admin@123")
    print("=" * 60)
    app.run(debug=True, port=5000)
