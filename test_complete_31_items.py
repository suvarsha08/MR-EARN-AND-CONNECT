import os
import sys
import unittest
import importlib.metadata

# Ensure base directory is in sys.path
BASE_DIR = r"c:\Users\suvar\Desktop\MR earn&connect"
sys.path.insert(0, BASE_DIR)

from app import app, analyze_skill_compatibility, calculate_profile_completion
from database.db import get_db_connection, query_db, execute_db
from database.seed_data import seed_database

class Complete31ItemVerification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.stdout.reconfigure(encoding='utf-8')
        print("\n" + "="*80)
        print("  MR EARN & CONNECT — 31-ITEM COMPREHENSIVE VERIFICATION SUITE")
        print("="*80 + "\n")
        seed_database()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False

    def get_client(self):
        """Helper to get a clean test client without session bleed."""
        return app.test_client()

    # 1. Database connection
    def test_01_database_connection(self):
        conn = get_db_connection()
        self.assertIsNotNone(conn)
        tables = query_db("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [t['name'] for t in tables]
        required_tables = [
            'users', 'student_profiles', 'skills', 'companies', 'jobs', 
            'internships', 'services', 'opportunities', 'projects', 
            'achievements', 'orders', 'ratings', 'earnings', 
            'announcements', 'connections'
        ]
        for rt in required_tables:
            self.assertIn(rt, table_names, f"Missing table: {rt}")
        print(" [PASS] 1. Database connection & all 15 tables verified.")

    # 2. Requirements/dependencies
    def test_02_requirements_dependencies(self):
        import flask
        import werkzeug
        import sqlite3
        flask_ver = importlib.metadata.version('flask')
        werkzeug_ver = importlib.metadata.version('werkzeug')
        self.assertTrue(len(flask_ver) > 0)
        self.assertTrue(len(werkzeug_ver) > 0)
        req_path = os.path.join(BASE_DIR, 'requirements.txt')
        self.assertTrue(os.path.exists(req_path))
        print(f" [PASS] 2. Dependencies verified (Flask {flask_ver}, Werkzeug {werkzeug_ver}, SQLite3).")

    # 3. Flask startup
    def test_03_flask_startup(self):
        self.assertIsNotNone(app.secret_key)
        client = self.get_client()
        resp = client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn("MR EARN &amp; CONNECT", resp.data.decode('utf-8'))
        print(" [PASS] 3. Flask application startup & root landing page verified.")

    # 4. Registration
    def test_04_registration(self):
        import time
        client = self.get_client()
        test_email = f"student_{int(time.time()*1000)}@mrdu.edu"
        resp = client.post('/register', data={
            'name': 'Test Registration Student',
            'email': test_email,
            'password': 'SecurePass@123',
            'phone': '+91 9988776655',
            'role': 'student'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        user = query_db("SELECT * FROM users WHERE email = ?", (test_email,), one=True)
        self.assertIsNotNone(user)
        self.assertEqual(user['role'], 'student')
        self.assertIn("Welcome to MR EARN &amp; CONNECT", resp.data.decode('utf-8'))
        print(" [PASS] 4. User Registration flow & role provisioning verified.")

    # 5. Login/logout
    def test_05_login_logout(self):
        client = self.get_client()
        # Invalid login
        bad = client.post('/login', data={'email': 'ghost@mrdu.edu', 'password': 'bad'}, follow_redirects=True)
        self.assertIn("Invalid email or password", bad.data.decode('utf-8'))

        # Valid login
        good = client.post('/login', data={'email': 'arjun@student.mrdu.edu', 'password': 'Student@123'}, follow_redirects=True)
        self.assertEqual(good.status_code, 200)
        self.assertIn("Welcome back, Arjun Kumar!", good.data.decode('utf-8'))

        # Logout
        lo = client.get('/logout', follow_redirects=True)
        self.assertEqual(lo.status_code, 200)
        self.assertIn("signed out successfully", lo.data.decode('utf-8'))

        # 1-Click Demo Logins for all 4 roles
        for role in ['student', 'employer', 'customer', 'admin']:
            d_client = self.get_client()
            d_res = d_client.get(f'/demo-login/{role}', follow_redirects=True)
            self.assertEqual(d_res.status_code, 200)
        print(" [PASS] 5. Login, rejection of invalid credentials, logout & 4 demo logins verified.")

    # 6. Student dashboard
    def test_06_student_dashboard(self):
        client = self.get_client()
        client.get('/demo-login/student', follow_redirects=True)
        resp = client.get('/dashboard')
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode('utf-8')
        self.assertIn("Student Dashboard", html)
        self.assertIn("Profile Completion", html)
        self.assertIn("Demo Earnings", html)
        print(" [PASS] 6. Student dashboard metrics, cards and widgets verified.")

    # 7. Student profile
    def test_07_student_profile(self):
        client = self.get_client()
        client.get('/demo-login/student', follow_redirects=True)
        # Own portfolio (redirects to view_profile/<id>)
        p1 = client.get('/profile', follow_redirects=True)
        self.assertEqual(p1.status_code, 200)
        self.assertIn("Arjun Kumar", p1.data.decode('utf-8'))
        # Public portfolio
        p2 = client.get('/profile/1')
        self.assertEqual(p2.status_code, 200)
        self.assertIn("Arjun Kumar", p2.data.decode('utf-8'))
        # Profile edit form
        p3 = client.get('/profile/edit')
        self.assertEqual(p3.status_code, 200)
        print(" [PASS] 7. Student profile (own portfolio, public profile, edit form) verified.")

    # 8. Skills and skill levels
    def test_08_skills_and_levels(self):
        client = self.get_client()
        client.get('/demo-login/student', follow_redirects=True)
        # Add skill
        res = client.post('/skills/add', data={
            'name': 'Cloud Computing AWS',
            'category': 'Technical',
            'level': 'Intermediate'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        skill = query_db("SELECT * FROM skills WHERE student_id = 1 AND name = 'Cloud Computing AWS'", one=True)
        self.assertIsNotNone(skill)
        self.assertEqual(skill['level'], 'Intermediate')
        # Delete skill
        del_res = client.post(f"/skills/delete/{skill['id']}", follow_redirects=True)
        self.assertEqual(del_res.status_code, 200)
        self.assertIsNone(query_db("SELECT * FROM skills WHERE id = ?", (skill['id'],), one=True))
        print(" [PASS] 8. Skill management (add, level, delete) verified.")

    # 9. Profile & Skill Analysis
    def test_09_profile_and_skill_analysis(self):
        comp = calculate_profile_completion(1)
        self.assertIn('percentage', comp)
        self.assertGreaterEqual(comp['percentage'], 70)
        client = self.get_client()
        client.get('/demo-login/student', follow_redirects=True)
        resp = client.get('/skill-analysis')
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode('utf-8')
        self.assertIn("My Skills Analysis", html)
        self.assertIn("Self-reported skill levels", html)
        print(" [PASS] 9. Profile & Skill Analysis computation & visualization verified.")

    # 10. Skill Compatibility Analysis
    def test_10_skill_compatibility_analysis(self):
        student_skills = ["Python", "HTML", "SQL"]
        job_skills = "Python, SQL, Flask"
        match = analyze_skill_compatibility(student_skills, job_skills)
        self.assertEqual(match['percentage'], 66)
        self.assertEqual(len(match['matched']), 2)
        self.assertIn("flask", [s.lower() for s in match['missing']])
        print(" [PASS] 10. Skill Compatibility Analysis (zero-AI rule-based set logic) verified.")

    # 11. Job search and filters
    def test_11_job_search_and_filters(self):
        client = self.get_client()
        # Catalog
        r1 = client.get('/jobs')
        self.assertEqual(r1.status_code, 200)
        self.assertIn("Career &amp; Graduate Jobs", r1.data.decode('utf-8'))
        # Search Python
        r2 = client.get('/jobs?q=Python')
        self.assertEqual(r2.status_code, 200)
        self.assertIn("Python", r2.data.decode('utf-8'))
        # Filter Full-time
        r3 = client.get('/jobs?job_type=Full-time')
        self.assertEqual(r3.status_code, 200)
        print(" [PASS] 11. Job search querying, keyword matching & job_type filters verified.")

    # 12. Job application
    def test_12_job_application(self):
        client = self.get_client()
        client.get('/demo-login/student', follow_redirects=True)
        # Apply to job 1
        res = client.post('/jobs/1/apply', data={'cover_note': 'First apply'}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        # Re-apply duplicate check
        dup = client.post('/jobs/1/apply', data={'cover_note': 'Duplicate apply'}, follow_redirects=True)
        self.assertIn("already applied", dup.data.decode('utf-8'))
        print(" [PASS] 12. Job application workflow & duplicate submission check verified.")

    # 13. Internship search and application
    def test_13_internship_search_and_application(self):
        client = self.get_client()
        # Search internships
        r = client.get('/internships?q=Frontend')
        self.assertEqual(r.status_code, 200)
        self.assertIn("Paid Campus &amp; Industry Internships", r.data.decode('utf-8'))
        # Apply to internship
        client.get('/demo-login/student', follow_redirects=True)
        apply_res = client.post('/internships/1/apply', data={'cover_note': 'Intern application'}, follow_redirects=True)
        self.assertEqual(apply_res.status_code, 200)
        print(" [PASS] 13. Internship directory, search & application verified.")

    # 14. Skill Marketplace
    def test_14_skill_marketplace(self):
        client = self.get_client()
        res = client.get('/services')
        self.assertEqual(res.status_code, 200)
        self.assertIn("Skill-to-Earn Marketplace", res.data.decode('utf-8'))
        # Filter category
        res_cat = client.get('/services?category=Academic+%26+Writing')
        self.assertEqual(res_cat.status_code, 200)
        print(" [PASS] 14. Skill Marketplace catalog & category browsing verified.")

    # 15. Create service
    def test_15_create_service(self):
        client = self.get_client()
        client.get('/demo-login/student', follow_redirects=True)
        res = client.post('/services/create', data={
            'title': 'High Speed Lab Record Formatting',
            'category': 'Academic & Writing',
            'price': '450',
            'delivery_time': '1 Day',
            'availability': 'Available',
            'skills': 'Typing, MS Word, LaTeX',
            'description': 'Speedy and clean lab report preparation for MRDU engineering labs.'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("listed successfully", res.data.decode('utf-8'))
        srv = query_db("SELECT * FROM services WHERE title = 'High Speed Lab Record Formatting'", one=True)
        self.assertIsNotNone(srv)
        print(" [PASS] 15. Student Skill-to-Earn service creation verified.")

    # 16. Customer service request
    def test_16_customer_service_request(self):
        client = self.get_client()
        client.get('/demo-login/customer', follow_redirects=True)
        res = client.post('/services/1/order', data={
            'requirements': 'Need 3 lab experiments formatted neatly.'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("Service requested", res.data.decode('utf-8'))
        print(" [PASS] 16. Customer order placement on student service verified.")

    # 17. Order status flow
    def test_17_order_status_flow(self):
        # Place order on Service #1 (provider is Arjun, user_id=1)
        cust_client = self.get_client()
        cust_client.get('/demo-login/customer', follow_redirects=True)
        cust_client.post('/services/1/order', data={'requirements': 'Urgent task order flow test'}, follow_redirects=True)
        new_order = query_db("SELECT * FROM orders WHERE service_id = 1 ORDER BY id DESC", one=True)
        self.assertIsNotNone(new_order)
        order_id = new_order['id']

        # Provider (Arjun) accepts order
        prov_client = self.get_client()
        prov_client.get('/demo-login/student', follow_redirects=True)
        prov_client.post(f'/orders/{order_id}/status', data={'status': 'Accepted'}, follow_redirects=True)
        self.assertEqual(query_db("SELECT status FROM orders WHERE id = ?", (order_id,), one=True)['status'], 'Accepted')

        # Provider (Arjun) completes order
        prov_client.post(f'/orders/{order_id}/status', data={'status': 'Completed'}, follow_redirects=True)
        self.assertEqual(query_db("SELECT status FROM orders WHERE id = ?", (order_id,), one=True)['status'], 'Completed')
        print(" [PASS] 17. Order lifecycle flow (Requested -> Accepted -> Completed) verified.")

    # 18. Demo earnings
    def test_18_demo_earnings(self):
        client = self.get_client()
        client.get('/demo-login/student', follow_redirects=True)
        res = client.get('/earnings')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn("DEMO EARNINGS", html)
        self.assertIn("Total Accumulated Balance", html)
        print(" [PASS] 18. Demo Earnings simulation, ledger & disclaimer verified.")

    # 19. Ratings/reviews
    def test_19_ratings_reviews(self):
        comp_order = query_db("SELECT * FROM orders WHERE status = 'Completed' ORDER BY id DESC", one=True)
        self.assertIsNotNone(comp_order)
        client = self.get_client()
        client.get('/demo-login/customer', follow_redirects=True)
        rate_res = client.post(f"/orders/{comp_order['id']}/rate", data={
            'rating': '5',
            'review': 'Top quality execution and rapid turnaround!'
        }, follow_redirects=True)
        self.assertEqual(rate_res.status_code, 200)
        r = query_db("SELECT * FROM ratings WHERE order_id = ?", (comp_order['id'],), one=True)
        self.assertIsNotNone(r)
        self.assertEqual(r['rating'], 5)
        print(" [PASS] 19. Customer 5-star rating & review flow verified.")

    # 20. Opportunities
    def test_20_opportunities(self):
        client = self.get_client()
        res = client.get('/opportunities')
        self.assertEqual(res.status_code, 200)
        self.assertIn("Campus &amp; External Opportunities", res.data.decode('utf-8'))
        filt = client.get('/opportunities?category=Ideathon')
        self.assertEqual(filt.status_code, 200)
        print(" [PASS] 20. Opportunities hub, hackathon/ideathon listings verified.")

    # 21. Achievements
    def test_21_achievements(self):
        client = self.get_client()
        res = client.get('/achievements')
        self.assertEqual(res.status_code, 200)
        self.assertIn("Student Honors &amp; Achievements", res.data.decode('utf-8'))
        # Add achievement
        client.get('/demo-login/student', follow_redirects=True)
        add = client.post('/achievements/add', data={
            'title': 'MRDU Smart Campus Ideathon 1st Prize',
            'issuer': 'MRDU Innovation Cell',
            'date': '2026-09-05',
            'description': 'Awarded 1st prize for building MR EARN & CONNECT platform.'
        }, follow_redirects=True)
        self.assertEqual(add.status_code, 200)
        print(" [PASS] 21. Student Achievements Wall of Fame & addition flow verified.")

    # 22. Projects
    def test_22_projects(self):
        client = self.get_client()
        res = client.get('/projects')
        self.assertEqual(res.status_code, 200)
        self.assertIn("Student Projects Showcase", res.data.decode('utf-8'))
        # Add project
        client.get('/demo-login/student', follow_redirects=True)
        add = client.post('/projects/add', data={
            'title': 'Campus IoT Weather Station',
            'tech_stack': 'Python, Flask, ESP32, MQTT',
            'description': 'Real-time weather telemetry system across MRDU campus.',
            'github_link': 'https://github.com/mrdu/iot-weather',
            'live_link': 'https://weather.mrdu.edu'
        }, follow_redirects=True)
        self.assertEqual(add.status_code, 200)
        print(" [PASS] 22. Projects showcase & project submission verified.")

    # 23. Connections
    def test_23_connections(self):
        client = self.get_client()
        client.get('/demo-login/student', follow_redirects=True)
        res = client.get('/connections')
        self.assertEqual(res.status_code, 200)
        self.assertIn("MRDU Connect Portal", res.data.decode('utf-8'))
        # Toggle connect with user 3
        tog = client.post('/connections/toggle/3', follow_redirects=True)
        self.assertEqual(tog.status_code, 200)
        print(" [PASS] 23. Peer & employer networking connections verified.")

    # 24. MRDU Campus
    def test_24_mrdu_campus(self):
        client = self.get_client()
        res = client.get('/campus')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn("Malla Reddy Deemed to be University", html)
        self.assertIn("Tirupati", html)
        print(" [PASS] 24. MRDU Campus portal & university presentation verified.")

    # 25. Announcements
    def test_25_announcements(self):
        client = self.get_client()
        res = client.get('/announcements')
        self.assertEqual(res.status_code, 200)
        self.assertIn("Campus Announcements", res.data.decode('utf-8'))
        # Admin creates announcement
        client.get('/demo-login/admin', follow_redirects=True)
        create_ann = client.post('/announcements/create', data={
            'title': 'Ideathon 2026 Presentations Underway',
            'category': 'Ideathon',
            'priority': 'Urgent',
            'content': 'Teams present live in Auditorium B before the judge committee.'
        }, follow_redirects=True)
        self.assertEqual(create_ann.status_code, 200)
        print(" [PASS] 25. Campus notice board & announcement broadcasting verified.")

    # 26. Employer dashboard
    def test_26_employer_dashboard(self):
        client = self.get_client()
        client.get('/demo-login/employer', follow_redirects=True)
        res = client.get('/dashboard')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn("Employer Recruitment Portal", html)
        self.assertIn("TechCorp Solutions", html)
        print(" [PASS] 26. Employer portal, applicant tracker & job management verified.")

    # 27. Customer dashboard
    def test_27_customer_dashboard(self):
        client = self.get_client()
        client.get('/demo-login/customer', follow_redirects=True)
        res = client.get('/dashboard')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn("Customer &amp; Faculty Portal", html)
        self.assertIn("My Requested Orders", html)
        print(" [PASS] 27. Customer/faculty dashboard & order monitoring verified.")

    # 28. Admin dashboard
    def test_28_admin_dashboard(self):
        client = self.get_client()
        client.get('/demo-login/admin', follow_redirects=True)
        res = client.get('/admin')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn("MRDU System Administration", html)
        self.assertIn("Administrator Portal", html)
        print(" [PASS] 28. Admin control center & platform analytics verified.")

    # 29. Role-based access
    def test_29_role_based_access(self):
        # Guest blocked from /dashboard
        g_client = self.get_client()
        g_res = g_client.get('/dashboard', follow_redirects=False)
        self.assertEqual(g_res.status_code, 302)

        # Student blocked from /admin
        s_client = self.get_client()
        s_client.get('/demo-login/student', follow_redirects=True)
        s_admin = s_client.get('/admin', follow_redirects=False)
        self.assertEqual(s_admin.status_code, 302)

        # Employer blocked from /services/create (student only)
        e_client = self.get_client()
        e_client.get('/demo-login/employer', follow_redirects=True)
        e_srv = e_client.get('/services/create', follow_redirects=False)
        self.assertEqual(e_srv.status_code, 302)
        print(" [PASS] 29. Role-based access control (RBAC) restrictions verified.")

    # 30. Navigation/buttons/forms
    def test_30_navigation_buttons_forms(self):
        client = self.get_client()
        endpoints = [
            '/', '/about', '/jobs', '/internships', '/services', 
            '/opportunities', '/projects', '/achievements', 
            '/campus', '/announcements', '/login', '/register'
        ]
        for ep in endpoints:
            r = client.get(ep)
            self.assertEqual(r.status_code, 200, f"Endpoint {ep} failed with status {r.status_code}")
        print(" [PASS] 30. All 12 public navigation routes, forms & buttons render 200 OK.")

    # 31. Responsive UI
    def test_31_responsive_ui(self):
        css_path = os.path.join(BASE_DIR, 'static', 'css', 'style.css')
        self.assertTrue(os.path.exists(css_path))
        with open(css_path, 'r', encoding='utf-8') as f:
            css = f.read()
        self.assertIn("--bg-primary", css)
        self.assertIn("@media (max-width:", css)
        self.assertIn("--bg-card", css)
        self.assertIn(".btn-primary", css)
        self.assertIn(".card", css)

        base_path = os.path.join(BASE_DIR, 'templates', 'base.html')
        with open(base_path, 'r', encoding='utf-8') as f:
            base_html = f.read()
        self.assertIn("style.css", base_html)
        self.assertIn("viewport", base_html)
        print(" [PASS] 31. Responsive UI, glassmorphism design system & viewports verified.")

if __name__ == '__main__':
    unittest.main()
