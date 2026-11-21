import http.server
import json
import os
import socketserver
import threading
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR
SHOTS_DIR = BASE_DIR / "tests" / "e2e_screenshots"
SHOTS_DIR.mkdir(parents=True, exist_ok=True)

# Clean offline utility CSS fallback so headless Chromium renders layouts crisply even without internet CDN
OFFLINE_CSS_FALLBACK = """
(function() {
  if (document.getElementById('e2e-offline-css')) return;
  const style = document.createElement('style');
  style.id = 'e2e-offline-css';
  style.textContent = `
    .hidden { display: none !important; }
    header nav.hidden { display: flex !important; }
    .flex { display: flex; }
    .inline-flex { display: inline-flex; }
    .grid { display: grid; }
    .block { display: block; }
    .flex-col { flex-direction: column; }
    .flex-wrap { flex-wrap: wrap; }
    .items-center { align-items: center; }
    .items-start { align-items: flex-start; }
    .justify-between { justify-content: space-between; }
    .justify-center { justify-content: center; }
    .justify-end { justify-content: flex-end; }
    .gap-1\\.5 { gap: 6px; }
    .gap-2 { gap: 8px; }
    .gap-2\\.5 { gap: 10px; }
    .gap-3 { gap: 12px; }
    .gap-4 { gap: 16px; }
    .gap-6 { gap: 24px; }
    .space-y-2 > * + * { margin-top: 8px; }
    .space-y-3 > * + * { margin-top: 12px; }
    .space-y-4 > * + * { margin-top: 16px; }
    .space-y-5 > * + * { margin-top: 20px; }
    .space-y-6 > * + * { margin-top: 24px; }
    .space-y-7 > * + * { margin-top: 28px; }
    .max-w-5xl, .max-w-6xl { max-width: 1040px; margin-left: auto; margin-right: auto; }
    .max-w-md { max-width: 440px; margin-left: auto; margin-right: auto; }
    .max-w-xl { max-width: 600px; margin-left: auto; margin-right: auto; }
    .w-full { width: 100%; }
    .min-h-screen { min-height: 100vh; }
    .mx-auto { margin-left: auto; margin-right: auto; }
    .p-4 { padding: 16px; }
    .p-5 { padding: 20px; }
    .p-6 { padding: 24px; }
    .p-8 { padding: 32px; }
    .px-3 { padding-left: 12px; padding-right: 12px; }
    .px-3\\.5 { padding-left: 14px; padding-right: 14px; }
    .px-4 { padding-left: 16px; padding-right: 16px; }
    .px-5 { padding-left: 20px; padding-right: 20px; }
    .px-6 { padding-left: 24px; padding-right: 24px; }
    .px-7 { padding-left: 28px; padding-right: 28px; }
    .py-1 { padding-top: 4px; padding-bottom: 4px; }
    .py-1\\.5 { padding-top: 6px; padding-bottom: 6px; }
    .py-2 { padding-top: 8px; padding-bottom: 8px; }
    .py-2\\.5 { padding-top: 10px; padding-bottom: 10px; }
    .py-3 { padding-top: 12px; padding-bottom: 12px; }
    .py-3\\.5 { padding-top: 14px; padding-bottom: 14px; }
    .py-4 { padding-top: 16px; padding-bottom: 16px; }
    .py-7 { padding-top: 28px; padding-bottom: 28px; }
    .pt-14 { padding-top: 56px; }
    .pb-12 { padding-bottom: 48px; }
    .mb-1\\.5 { margin-bottom: 6px; }
    .mt-1 { margin-top: 4px; }
    .h-16 { height: 64px; }
    .w-9 { width: 36px; height: 36px; }
    .w-12 { width: 48px; height: 48px; }
    .rounded-xl { border-radius: 12px; }
    .rounded-2xl { border-radius: 16px; }
    .rounded-3xl { border-radius: 24px; }
    .rounded-full { border-radius: 9999px; }
    .text-center { text-align: center; }
    .text-right { text-align: right; }
    .text-left { text-align: left; }
    .text-xs { font-size: 12px; }
    .text-sm { font-size: 14px; }
    .text-base { font-size: 16px; }
    .text-xl { font-size: 20px; }
    .text-2xl { font-size: 24px; }
    .text-3xl { font-size: 34px; }
    .font-bold, .font-extrabold { font-weight: 700; }
    .font-semibold { font-weight: 600; }
    .font-mono { font-family: monospace; }
    .grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .sm\\:grid-cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
    .sm\\:grid-cols-12 { grid-template-columns: repeat(12, minmax(0, 1fr)); }
    .md\\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .lg\\:grid-cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
    .sm\\:col-span-4 { grid-column: span 4 / span 4; }
    .sm\\:col-span-3 { grid-column: span 3 / span 3; }
    .sm\\:col-span-2 { grid-column: span 2 / span 2; }
    .sm\\:col-span-1 { grid-column: span 1 / span 1; }
    .md\\:flex { display: flex; }
    .md\\:hidden { display: none !important; }
    .sm\\:block { display: block; }
    .sm\\:hidden { display: none !important; }
    .fixed { position: fixed; }
    .inset-0 { top: 0; right: 0; bottom: 0; left: 0; }
    .z-50 { z-index: 50; }
    .bg-black\\/70 { background-color: rgba(0, 0, 0, 0.72); }
    button { cursor: pointer; font-family: inherit; border: none; }
    input, select, textarea { box-sizing: border-box; font-family: inherit; }
  `;
  document.head.appendChild(style);
})();
"""

import re
class QuietHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        html = (OUTPUT_DIR / "index.html").read_text(encoding="utf-8")
        # Strip external CDN links in offline test environment so headless Chrome never stalls
        html = re.sub(r'<script src="https?://[^"]+"></script>', '', html)
        html = re.sub(r'<link [^>]*href="https?://[^"]+"[^>]*>', '', html)
        html = html.replace('tailwind.config = {', 'window._tw = {')
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, format, *args):
        pass

def start_server():
    httpd = socketserver.TCPServer(("127.0.0.1", 0), QuietHandler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, port

def run_e2e():
    html = (OUTPUT_DIR / "index.html").read_text(encoding="utf-8")
    html = re.sub(r'<script src="https?://[^"]+"></script>', '', html)
    html = re.sub(r'<link [^>]*href="https?://[^"]+"[^>]*>', '', html)
    html = html.replace('tailwind.config = {', 'window._tw = {')
    offline_html = SHOTS_DIR / "e2e_offline_target.html"
    offline_html.write_text(html, encoding="utf-8")
    url = offline_html.as_uri()
    httpd = None
    results = []

    opts = Options()
    opts.page_load_strategy = "eager"
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1280,940")
    driver = webdriver.Chrome(options=opts)
    wait = WebDriverWait(driver, 10)

    def ensure_css():
        driver.execute_script(OFFLINE_CSS_FALLBACK)

    def snap(filename):
        ensure_css()
        time.sleep(0.25)
        driver.save_screenshot(str(SHOTS_DIR / filename))

    def login_as(username, password):
        wait.until(EC.visibility_of_element_located((By.ID, "loginUsername")))
        u_el = driver.find_element(By.ID, "loginUsername")
        p_el = driver.find_element(By.ID, "loginPassword")
        u_el.clear()
        u_el.send_keys(username)
        p_el.clear()
        p_el.send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "#loginForm button[type='submit']").click()
        wait.until(EC.visibility_of_element_located((By.ID, "appView")))
        ensure_css()

    try:
        # STEP 1: Landing Page Render & Navigation to Login
        t0 = time.time()
        driver.get(url)
        ensure_css()
        wait.until(EC.visibility_of_element_located((By.ID, "landingView")))
        hero_h1 = driver.find_element(By.CSS_SELECTOR, "#landingView h1").text
        assert "تحویل پروژه‌های دانشگاهی" in hero_h1
        snap("step1_landing.png")
        driver.find_element(By.ID, "landingHeroLoginBtn").click()
        wait.until(EC.visibility_of_element_located((By.ID, "loginView")))
        results.append({
            "step": "E2E-01",
            "title": "Landing Page & Login Navigation",
            "detail": "Verified minimal landing page renders and transitions to clean login form.",
            "status": "PASS",
            "ms": int((time.time() - t0) * 1000),
            "shot": "step1_landing.png"
        })

        # STEP 2: Student Login + Course Dropdown Auto-Professor + New Project Upload
        t0 = time.time()
        login_as("stu", "321")
        assert driver.find_element(By.ID, "headerUserFullName").text == "آریا رادمنش"
        driver.find_element(By.ID, "studentQuickNewProjectBtn").click()
        wait.until(EC.visibility_of_element_located((By.ID, "sectionStudentUpload")))

        course_select = Select(driver.find_element(By.ID, "stuClassNameInput"))
        course_select.select_by_visible_text("سیستم‌های توزیع‌شده")
        wait.until(EC.visibility_of_element_located((By.ID, "autoProfessorCard")))
        auto_prof = driver.find_element(By.ID, "autoProfessorNameText").text
        assert auto_prof == "دکتر ماندانا کاظمی", f"Expected دکتر ماندانا کاظمی, got {auto_prof}"

        driver.find_element(By.ID, "stuProjectNameInput").send_keys("سامانه پایش کلاستر Kubernetes")
        driver.find_element(By.ID, "stuVersionInput").clear()
        driver.find_element(By.ID, "stuVersionInput").send_keys("v1.0")
        driver.find_element(By.ID, "stuDescriptionInput").send_keys("مانیتورینگ لحظه‌ای نودها با Prometheus و داشبورد هشدار خودکار.")
        snap("step2_student_upload.png")

        driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", driver.find_element(By.CSS_SELECTOR, "#studentNewProjectForm button[type='submit']"))
        wait.until(EC.visibility_of_element_located((By.ID, "sectionProjectsList")))
        assert "سامانه پایش کلاستر Kubernetes" in driver.find_element(By.ID, "projectsListContainer").text
        results.append({
            "step": "E2E-02",
            "title": "Student Upload & Auto-Professor Dropdown",
            "detail": "Selected course auto-revealed 'دکتر ماندانا کاظمی' and submitted new project v1.0.",
            "status": "PASS",
            "ms": int((time.time() - t0) * 1000),
            "shot": "step2_student_upload.png"
        })

        # STEP 3: Strict Isolation Check — Professor 1 MUST NOT see Professor 2's project
        t0 = time.time()
        driver.find_element(By.ID, "logoutBtn").click()
        wait.until(EC.visibility_of_element_located((By.ID, "landingView")))
        driver.find_element(By.ID, "landingHeaderLoginBtn").click()
        login_as("admin", "123")
        assert driver.find_element(By.ID, "headerUserFullName").text == "دکتر سهراب فرزانه"
        prof1_text = driver.find_element(By.ID, "projectsListContainer").text
        assert "سامانه پایش کلاستر Kubernetes" not in prof1_text, "Isolation breach: Prof 1 saw Prof 2 project!"
        assert "تشخیص تعاملات دارویی" in prof1_text
        snap("step3_prof1_isolation.png")
        results.append({
            "step": "E2E-03",
            "title": "Professor 1 Panel Isolation Verification",
            "detail": "Logged in as admin/123 (Prof 1); verified Prof 2's project is strictly hidden.",
            "status": "PASS",
            "ms": int((time.time() - t0) * 1000),
            "shot": "step3_prof1_isolation.png"
        })

        # STEP 4: Professor 2 Login + Inspect & Grade Newly Uploaded Project
        t0 = time.time()
        driver.find_element(By.ID, "logoutBtn").click()
        wait.until(EC.visibility_of_element_located((By.ID, "landingView")))
        driver.find_element(By.ID, "landingHeaderLoginBtn").click()
        login_as("prof2", "123")
        assert driver.find_element(By.ID, "headerUserFullName").text == "دکتر ماندانا کاظمی"
        rows = driver.find_elements(By.CSS_SELECTOR, "[data-project-row]")
        target_row = [r for r in rows if "سامانه پایش کلاستر Kubernetes" in r.text][0]
        target_row.click()
        wait.until(EC.visibility_of_element_located((By.ID, "sectionProjectDetail")))

        score_inp = driver.find_element(By.ID, "profScoreInput")
        score_inp.clear()
        score_inp.send_keys("19.5")
        Select(driver.find_element(By.ID, "profStatusSelect")).select_by_value("approved")
        comment_inp = driver.find_element(By.ID, "profCommentInput")
        comment_inp.clear()
        comment_inp.send_keys("معماری پایش کلاستر بسیار دقیق و قابل دفاع در سطح عالی است.")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", driver.find_element(By.CSS_SELECTOR, "#profEvaluationForm button[type='submit']"))
        time.sleep(0.2)
        assert "19.5 / 20" in driver.find_element(By.ID, "detailScoreDisplay").text
        snap("step4_prof2_grading.png")
        results.append({
            "step": "E2E-04",
            "title": "Professor 2 Grading & Approval",
            "detail": "Logged in as prof2/123; graded Kubernetes project 19.5/20 and approved.",
            "status": "PASS",
            "ms": int((time.time() - t0) * 1000),
            "shot": "step4_prof2_grading.png"
        })

        # STEP 5: Student Verifies Grade & Opens Printable Evaluation Report
        t0 = time.time()
        driver.find_element(By.ID, "logoutBtn").click()
        wait.until(EC.visibility_of_element_located((By.ID, "landingView")))
        driver.find_element(By.ID, "landingHeaderLoginBtn").click()
        login_as("stu", "321")
        rows = driver.find_elements(By.CSS_SELECTOR, "[data-project-row]")
        target_row = [r for r in rows if "سامانه پایش کلاستر Kubernetes" in r.text][0]
        target_row.click()
        wait.until(EC.visibility_of_element_located((By.ID, "sectionProjectDetail")))
        assert "19.5 از ۲۰" in driver.find_element(By.ID, "stuViewScore").text
        driver.find_element(By.ID, "openReportModalBtn").click()
        wait.until(EC.visibility_of_element_located((By.ID, "reportModal")))
        snap("step5_student_report.png")
        driver.find_element(By.ID, "closeReportModalBtn").click()
        results.append({
            "step": "E2E-05",
            "title": "Student Grade & Official Report Modal",
            "detail": "Student saw updated 19.5/20 grade, feedback, and printable evaluation report.",
            "status": "PASS",
            "ms": int((time.time() - t0) * 1000),
            "shot": "step5_student_report.png"
        })

        # STEP 6: Account Profile Update & Light Mode Toggle
        t0 = time.time()
        driver.find_element(By.ID, "navAccountBtn").click()
        wait.until(EC.visibility_of_element_located((By.ID, "sectionAccount")))
        name_inp = driver.find_element(By.ID, "accDisplayName")
        name_inp.clear()
        name_inp.send_keys("آریا رادمنش (ارشد)")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", driver.find_element(By.CSS_SELECTOR, "#accountSettingsForm button[type='submit']"))
        time.sleep(0.2)
        assert driver.find_element(By.ID, "headerUserFullName").text == "آریا رادمنش (ارشد)"
        driver.find_element(By.CSS_SELECTOR, "#appView [data-theme-toggle]").click()
        time.sleep(0.2)
        assert "light" in driver.find_element(By.TAG_NAME, "html").get_attribute("class")
        snap("step6_account_lightmode.png")
        results.append({
            "step": "E2E-06",
            "title": "Account Profile Update & Light Mode",
            "detail": "Updated display name live in top header and switched to standard Light Mode.",
            "status": "PASS",
            "ms": int((time.time() - t0) * 1000),
            "shot": "step6_account_lightmode.png"
        })

    finally:
        driver.quit()
        if httpd: httpd.shutdown()

    out_json = SHOTS_DIR / "e2e_results.json"
    out_json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"E2E_COMPLETED: {len(results)}/{len(results)} PASSED")

if __name__ == "__main__":
    run_e2e()
