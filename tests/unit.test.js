const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

// Extract the application's core script from aurelia_academe_portal.html
const htmlPath = path.resolve(__dirname, '../index.html');
const htmlContent = fs.readFileSync(htmlPath, 'utf8');
const scripts = [...htmlContent.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const appScript = scripts[scripts.length - 1];

// Create a lightweight sandboxed runtime for pure unit testing of core functions & state
function createAppRuntime() {
  const storage = new Map();
  const sandbox = {
    window: {
      addEventListener: () => {},
      scrollTo: () => {},
      lucide: null
    },
    document: {
      getElementById: () => ({
        textContent: '',
        value: '',
        className: '',
        classList: { add: () => {}, remove: () => {}, toggle: () => {} }
      }),
      querySelectorAll: () => []
    },
    localStorage: {
      getItem: (k) => (storage.has(k) ? storage.get(k) : null),
      setItem: (k, v) => storage.set(k, String(v))
    },
    setTimeout: () => {},
    console
  };
  vm.createContext(sandbox);
  vm.runInContext(appScript + "\n;globalThis.appState = appState; globalThis.COURSE_CATALOG = COURSE_CATALOG; globalThis.STORAGE_KEY = STORAGE_KEY;", sandbox);
  return sandbox;
}

test('UT-01: Default accounts define 3 professors and 1 student with valid credentials', () => {
  const rt = createAppRuntime();
  const acc = rt.appState.data.accounts;

  assert.equal(acc.prof1.username, 'admin');
  assert.equal(acc.prof1.password, '123');
  assert.equal(acc.prof1.role, 'professor');

  assert.equal(acc.prof2.username, 'prof2');
  assert.equal(acc.prof2.password, '123');
  assert.equal(acc.prof2.role, 'professor');

  assert.equal(acc.prof3.username, 'prof3');
  assert.equal(acc.prof3.password, '123');
  assert.equal(acc.prof3.role, 'professor');

  assert.equal(acc.student.username, 'stu');
  assert.equal(acc.student.password, '321');
  assert.equal(acc.student.role, 'student');
});

test('UT-02: Course catalog maps every course cleanly to one of the 3 professors', () => {
  const rt = createAppRuntime();
  const catalog = rt.COURSE_CATALOG;
  const accounts = rt.appState.data.accounts;

  assert.equal(catalog.length, 6);
  for (const item of catalog) {
    assert.ok(accounts[item.professorKey], `Missing account for ${item.professorKey}`);
    assert.equal(accounts[item.professorKey].role, 'professor');
  }

  const distCourse = catalog.find(c => c.course === 'سیستم‌های توزیع‌شده');
  assert.equal(distCourse.professorKey, 'prof2');
  assert.equal(accounts[distCourse.professorKey].displayName, 'دکتر ماندانا کاظمی');
});

test('UT-03: Strict per-professor project scoping isolates each professor panel', () => {
  const rt = createAppRuntime();

  rt.appState.currentAccountKey = 'prof1';
  rt.appState.currentUserRole = 'professor';
  const prof1Projects = rt.getScopedProjects();
  assert.equal(prof1Projects.length, 1);
  assert.ok(prof1Projects.every(p => p.professorKey === 'prof1'));

  rt.appState.currentAccountKey = 'prof2';
  rt.appState.currentUserRole = 'professor';
  const prof2Projects = rt.getScopedProjects();
  assert.equal(prof2Projects.length, 1);
  assert.ok(prof2Projects.every(p => p.professorKey === 'prof2'));

  rt.appState.currentAccountKey = 'prof3';
  rt.appState.currentUserRole = 'professor';
  const prof3Projects = rt.getScopedProjects();
  assert.equal(prof3Projects.length, 1);
  assert.ok(prof3Projects.every(p => p.professorKey === 'prof3'));
});

test('UT-04: Student role has visibility over all submitted projects across all professors', () => {
  const rt = createAppRuntime();
  rt.appState.currentAccountKey = 'student';
  rt.appState.currentUserRole = 'student';

  const studentProjects = rt.getScopedProjects();
  assert.equal(studentProjects.length, 3);
  const profKeys = new Set(studentProjects.map(p => p.professorKey));
  assert.deepEqual([...profKeys].sort(), ['prof1', 'prof2', 'prof3']);
});

test('UT-05: History and notifications are strictly scoped to the logged-in professor', () => {
  const rt = createAppRuntime();

  rt.appState.currentAccountKey = 'prof1';
  rt.appState.currentUserRole = 'professor';
  const prof1History = rt.getScopedHistory();
  const prof1Notifs = rt.getAllNotifications();
  assert.ok(prof1History.length > 0);
  assert.ok(prof1History.every(h => h.professorKey === 'prof1'));
  assert.ok(prof1Notifs.every(n => n.projectId === 'PRJ-101'));

  rt.appState.currentAccountKey = 'prof2';
  const prof2Notifs = rt.getAllNotifications();
  assert.ok(prof2Notifs.every(n => n.projectId === 'PRJ-102'));
});

test('UT-06: Status badge resolver returns exact labels and CSS classes for all 3 states', () => {
  const rt = createAppRuntime();

  assert.deepEqual({ ...rt.getStatusInfo('approved') }, { label: 'تایید نهایی', cls: 'badge-approved' });
  assert.deepEqual({ ...rt.getStatusInfo('revision') }, { label: 'نیاز به اصلاح', cls: 'badge-revision' });
  assert.deepEqual({ ...rt.getStatusInfo('pending') }, { label: 'در انتظار بررسی', cls: 'badge-pending' });
});

test('UT-07: Data persistence saves and reloads modified grades and accounts in localStorage', () => {
  const rt = createAppRuntime();
  rt.appState.data.projects[0].score = 20;
  rt.appState.data.accounts.prof1.displayName = 'دکتر فرزانه (ویرایش‌شده)';
  rt.persistData();

  const raw = rt.localStorage.getItem(rt.STORAGE_KEY);
  assert.ok(raw, 'Expected serialized state in localStorage');
  const parsed = JSON.parse(raw);
  assert.equal(parsed.projects[0].score, 20);
  assert.equal(parsed.accounts.prof1.displayName, 'دکتر فرزانه (ویرایش‌شده)');
});

test('UT-08: Resetting default data restores clean initial state', () => {
  const rt = createAppRuntime();
  rt.appState.data.projects = [];
  assert.equal(rt.appState.data.projects.length, 0);

  rt.appState.data = rt.getDefaultData();
  assert.equal(rt.appState.data.projects.length, 3);
  assert.equal(rt.appState.data.accounts.student.username, 'stu');
});
