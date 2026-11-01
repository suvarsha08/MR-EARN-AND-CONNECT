import unittest
import os
import sys

from werkzeug.security import check_password_hash
from app import app, analyze_skill_compatibility, calculate_profile_completion
from database.db import get_db_connection, query_db, execute_db
from database.seed_data import seed_database

class TestMREarnAndConnect(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Seed fresh database
        seed_database()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        cls.client = app.test_client()

    def test_01_database_seed_counts(self):
        """Test database table counts."""
        tables = {
            'users': 10,
            'student_profiles': 5,
            'skills': 26,
            'companies': 3,
            'jobs': 8,
            'internships': 6,
            'services': 8,
            'opportunities': 8,
            'projects': 5,
            'achievements': 5,
            'orders': 2,
            'ratings': 2,
            'earnings': 2,
            'announcements': 4,
            'connections': 5
        }
        for table, expected_min in tables.items():
            count = query_db(f"SELECT COUNT(*) as cnt FROM {table}", one=True)['cnt']
            self.assertGreaterEqual(count, expected_min, f"Table {table} count ({count}) is less than {expected_min}")

    def test_02_transparent_skill_compatibility_logic(self):
        """
        Critical Test: Ensure NO AI is used.
        Verify deterministic Python string/set comparison logic:
        Student: Python, HTML, SQL
        Job: Python, SQL, Flask
        Result: 66% match (Python, SQL matched; Flask missing).
        """
        student_skills = ["Python", "HTML", "SQL", "Typing", "Record Writing"]
        job_skills = "Python, SQL, Flask"
        result = analyze_skill_compatibility(student_skills, job_skills)

        self.assertEqual(result['percentage'], 66)
        self.assertIn("Python", result['matched'])
        self.assertIn("Sql", [s.title() for s in result['matched']])
        self.assertIn("Flask", [s.title() for s in result['missing']])
        self.assertEqual(result['total_required'], 3)

    def test_03_profile_completion_calculation(self):
        """Verify profile completion logic for Arjun (user_id=1)."""
        completion = calculate_profile_completion(1)
        self.assertGreaterEqual(completion['percentage'], 80)
        self.assertEqual(len(completion['breakdown']), 7)

    def test_04_public_routes(self):
        """Test public routes accessibility."""
        routes = ['/', '/about', '/jobs', '/internships', '/services', '/opportunities', '/projects', '/achievements', '/campus', '/announcements', '/login', '/register']
        for route in routes:
            resp = self.client.get(route)
            self.assertEqual(resp.status_code, 200, f"Route {route} returned {resp.status_code}")

    def test_05_auth_flow(self):
        """Test register, login, demo-login, and logout."""
        # 1. Login with demo student
        resp = self.client.post('/login', data={
            'email': 'arjun@student.mrdu.edu',
            'password': 'Student@123'
        }, follow_redirects=True)
        self.assertIn(b"Welcome back", resp.data)

        # 2. Access dashboard
        dash_resp = self.client.get('/dashboard')
        self.assertEqual(dash_resp.status_code, 200)
        self.assertIn(b"Profile Completion", dash_resp.data)

        # 3. Logout
        logout_resp = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b"signed out", logout_resp.data)

        # 4. Instant Demo Login (Employer)
        emp_resp = self.client.get('/demo-login/employer', follow_redirects=True)
        self.assertEqual(emp_resp.status_code, 200)
        self.assertIn(b"TechCorp Solutions", emp_resp.data)

    def test_06_17_step_ideathon_demo_flow(self):
        """
        End-to-End simulation of the 17-Step Winning Ideathon Demo Flow:
        Step 1: Student registers
        Step 2: Build Profile
        Step 3: Skill Levels
        Step 4: Profile Analysis
        Step 5: Find a Job
        Step 6: Skill Compatibility
        Step 7: Apply
        Step 8: Find Internship & Apply
        Step 9: Create Service (Skill-to-Earn)
        Step 10: Customer discovers service
        Step 11: Customer requests order
        Step 12: Provider accepts & completes order
        Step 13: Demo Earnings updated
        Step 14: Customer rates 5 stars with review
        Step 15: Student Portfolio display
        Step 16: Connect with user
        Step 17: Admin dashboard review
        """
        # Step 1: Student registers (new student: Vikranth Kumar)
        self.client.get('/logout')
        reg_resp = self.client.post('/register', data={
            'name': 'Vikranth Kumar',
            'email': 'vikranth@student.mrdu.edu',
            'password': 'Student@123',
            'phone': '+91 9123456789',
            'role': 'student'
        }, follow_redirects=True)
        self.assertEqual(reg_resp.status_code, 200)
        
        user_row = query_db("SELECT id FROM users WHERE email = 'vikranth@student.mrdu.edu'", one=True)
        self.assertIsNotNone(user_row)
        vikranth_id = user_row['id']

        # Step 2: Build Profile
        self.client.post('/profile/edit', data={
            'name': 'Vikranth Kumar',
            'phone': '+91 9123456789',
            'college': 'Malla Reddy Deemed to be University, Tirupati',
            'department': 'Computer Science & Engineering',
            'course': 'B.Tech CSE-AIML',
            'year': '1st Year',
            'education': '12th Science 93%',
            'cgpa': '9.0',
            'bio': 'Passionate first year CSE-AIML student proficient in Python, SQL, and record writing.',
            'resume': 'https://drive.google.com/vikranth_resume',
            'preferred_job_type': 'Full-time / Internship',
            'preferred_location': 'Tirupati / Remote'
        }, follow_redirects=True)

        # Step 3: Add Skills with Levels
        skills_to_add = [
            ("Python", "Technical", "Advanced"),
            ("HTML", "Technical", "Intermediate"),
            ("SQL", "Technical", "Intermediate"),
            ("Typing", "Digital", "Advanced"),
            ("Record Writing", "Digital", "Advanced")
        ]
        for s_name, s_cat, s_lvl in skills_to_add:
            self.client.post('/skills/add', data={
                'name': s_name,
                'category': s_cat,
                'level': s_lvl
            }, follow_redirects=True)

        # Step 4: Open Skill Analysis
        analysis_resp = self.client.get('/skill-analysis')
        self.assertEqual(analysis_resp.status_code, 200)
        self.assertIn(b"My Skills Analysis", analysis_resp.data)
        self.assertIn(b"Self-reported skill levels", analysis_resp.data)

        # Step 5: Find a Job (Search Python Developer)
        search_resp = self.client.get('/jobs?q=Python+Developer')
        self.assertEqual(search_resp.status_code, 200)
        self.assertIn(b"Python Developer", search_resp.data)

        # Step 6: Skill Compatibility on Job #1
        job_resp = self.client.get('/jobs/1')
        self.assertEqual(job_resp.status_code, 200)
        self.assertIn(b"Skill Compatibility Analysis", job_resp.data)
        self.assertIn(b"66% Skill Compatibility", job_resp.data) # 2 out of 3 (Python, SQL vs Python, SQL, Flask)
        self.assertIn(b"Flask", job_resp.data) # Skills to develop

        # Step 7: Apply to Job #1
        apply_resp = self.client.post('/jobs/1/apply', data={
            'cover_note': 'I have strong Python and SQL skills and am currently learning Flask!'
        }, follow_redirects=True)
        self.assertIn(b"Application submitted successfully", apply_resp.data)

        # Step 8: Apply to Internship #1
        intern_apply = self.client.post('/internships/1/apply', data={
            'cover_note': 'Passionate about Python backend development.'
        }, follow_redirects=True)
        self.assertIn(b"Internship application submitted", intern_apply.data)

        # Step 9: Turn Skills into Earnings - Create Service
        srv_resp = self.client.post('/services/create', data={
            'title': 'Record Writing & Document Formatting',
            'category': 'Academic & Writing',
            'price': '500',
            'delivery_time': '2 Days',
            'availability': 'Available',
            'skills': 'Typing, MS Word, Formatting, Record Writing',
            'description': 'Neat, precise lab record writing and document formatting according to MRDU guidelines.'
        }, follow_redirects=True)
        self.assertIn(b"listed successfully", srv_resp.data)

        created_srv = query_db("SELECT id FROM services WHERE provider_id = ? ORDER BY id DESC", (vikranth_id,), one=True)
        self.assertIsNotNone(created_srv)
        srv_id = created_srv['id']

        # Step 10: Switch to Customer (Prof. Sharma) & discover service
        self.client.get('/logout')
        self.client.get('/demo-login/customer')

        srv_detail = self.client.get(f'/services/{srv_id}')
        self.assertEqual(srv_detail.status_code, 200)
        self.assertIn(b"Record Writing &amp; Document Formatting", srv_detail.data)

        # Step 11: Customer requests service order
        order_resp = self.client.post(f'/services/{srv_id}/order', data={
            'requirements': 'Format 10 pages of CSE Physics observation data and write clean record diagrams.'
        }, follow_redirects=True)
        self.assertIn(b"Service requested", order_resp.data)

        created_order = query_db("SELECT id FROM orders WHERE service_id = ? ORDER BY id DESC", (srv_id,), one=True)
        self.assertIsNotNone(created_order)
        order_id = created_order['id']

        # Step 12: Switch back to Student Provider (Vikranth) -> Accept & Complete order
        self.client.get('/logout')
        self.client.post('/login', data={'email': 'vikranth@student.mrdu.edu', 'password': 'Student@123'})
        
        # Provider accepts order
        self.client.post(f'/orders/{order_id}/status', data={'status': 'Accepted'}, follow_redirects=True)
        order_status = query_db("SELECT status FROM orders WHERE id = ?", (order_id,), one=True)['status']
        self.assertEqual(order_status, 'Accepted')

        # Provider completes order
        comp_resp = self.client.post(f'/orders/{order_id}/status', data={'status': 'Completed'}, follow_redirects=True)
        self.assertIn(b"Completed", comp_resp.data)

        # Step 13: Check Demo Earnings
        earnings_resp = self.client.get('/earnings')
        self.assertEqual(earnings_resp.status_code, 200)
        self.assertIn(b"500", earnings_resp.data)
        self.assertIn(b"DEMO EARNINGS", earnings_resp.data)

        # Step 14: Customer leaves 5-star rating & review
        self.client.get('/logout')
        self.client.get('/demo-login/customer')
        rate_resp = self.client.post(f'/orders/{order_id}/rate', data={
            'rating': '5',
            'review': 'Immaculate record writing and delivered in 24 hours. Highly recommended!'
        }, follow_redirects=True)
        self.assertIn(b"5-star rating", rate_resp.data)

        # Step 15: Check Student Portfolio
        port_resp = self.client.get(f'/profile/{vikranth_id}')
        self.assertEqual(port_resp.status_code, 200)
        self.assertIn(b"Vikranth Kumar", port_resp.data)
        self.assertIn(b"Immaculate record writing", port_resp.data)

        # Step 16: Connect with employer (TechCorp - user_id=6)
        conn_resp = self.client.post('/connections/toggle/6', follow_redirects=True)
        self.assertEqual(conn_resp.status_code, 200)

        # Step 17: Admin Dashboard Review
        self.client.get('/logout')
        self.client.get('/demo-login/admin')
        admin_resp = self.client.get('/admin')
        self.assertEqual(admin_resp.status_code, 200)
        self.assertIn(b"MRDU System Administration", admin_resp.data)
        self.assertIn(b"Total Registered Users", admin_resp.data)

if __name__ == '__main__':
    unittest.main()
