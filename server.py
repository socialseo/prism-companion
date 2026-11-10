#!/usr/bin/env python3
"""PRISM Companion: prototipo LAN, solo libreria standard Python."""
import json, sqlite3, secrets, datetime, os, argparse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
ROOT = Path(__file__).resolve().parent
DB = os.environ.get('PRISM_DB', str(ROOT / 'prism.sqlite3'))
HUMAN = dict(FOR='Forza', DES='Destrezza', COS='Costituzione', INT='Intelligenza', PER='Percezione', CAR='Carisma')
PILOT = dict(MIS='Precisione in mischia', TIR='Precisione a distanza', EVA='Evasione', DIF='Difesa', TEC='Tecnica', REA='Reattività')
SKILLS = 'Atletica,Acrobazia,Lotta,Armi bianche,Armi da fuoco,Furtività,Meccanica,Informatica,Elettronica,Medicina,Investigazione,Conoscenze militari,Osservazione,Intuizione,Sopravvivenza,Orientamento,Persuasione,Inganno,Intimidazione,Comando'.split(',')
FIELDS = {'personaggio': ('Nome personaggio', 'text'), 'mecha': ('Nome / modello mecha', 'text'), 'note': ('Equipaggiamento, condizioni e note', 'text'), 'HP umano': ('Punti salute umani', 'int', -100000, 25), **{k:(v,'int',1,20) for k,v in HUMAN.items()}, **{k:(v,'int',1,100) for k,v in PILOT.items()}, **{k:(k,'int',0,5) for k in SKILLS}, 'ARM': ('Armatura attuale', 'int',0,100000), 'ARM max':('Armatura massima','int',0,100000), 'HP mecha':('Integrità attuale','int',0,100000), 'HP max mecha':('Integrità massima','int',1,100000), 'EN':('Energia attuale','int',0,100000), 'EN max':('Energia massima','int',0,100000), 'MOB':('Mobilità','int',0,100000), 'MOV':('Movimento mecha','int',0,100000), 'SEN':('Sensori','int',0,50)}
def initial():
    d={k: ('' if v[1]=='text' else v[2]) for k,v in FIELDS.items()}
    d.update({k:10 for k in HUMAN}); d.update({k:50 for k in PILOT}); d.update({'HP umano':15,'HP mecha':100,'HP max mecha':100,'personaggio':'Nuovo personaggio','mecha':'Da configurare'})
    return d

def connect():
    c=sqlite3.connect(DB, timeout=10); c.row_factory=sqlite3.Row; return c

def init():
    with connect() as c:
        c.executescript('''CREATE TABLE IF NOT EXISTS sessions(code TEXT PRIMARY KEY, name TEXT);
        CREATE TABLE IF NOT EXISTS members(id TEXT PRIMARY KEY, code TEXT, name TEXT, role TEXT, token TEXT UNIQUE);
        CREATE TABLE IF NOT EXISTS sheets(owner TEXT PRIMARY KEY, data TEXT, version INTEGER);
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT, owner TEXT, actor TEXT, time TEXT, kind TEXT, changes TEXT, reason TEXT);''')
        if 'ready' not in [r[1] for r in c.execute('PRAGMA table_info(sheets)')]: c.execute('ALTER TABLE sheets ADD COLUMN ready INTEGER NOT NULL DEFAULT 0')
        if 'phase' not in [r[1] for r in c.execute('PRAGMA table_info(sessions)')]: c.execute("ALTER TABLE sessions ADD COLUMN phase TEXT NOT NULL DEFAULT 'Preparazione'")

def event(c, code, owner, actor, kind, changes, reason=''):
    c.execute('INSERT INTO events(code,owner,actor,time,kind,changes,reason) VALUES(?,?,?,?,?,?,?)',(code,owner,actor,datetime.datetime.now(datetime.timezone.utc).isoformat(),kind,json.dumps(changes),reason))

class Problem(Exception):
    def __init__(self, status, msg): self.status,self.msg=status,msg

def require(ok, msg, status=400):
    if not ok: raise Problem(status,msg)

def label(value, maximum=80):
    require(isinstance(value,str) and 0<len(value.strip())<=maximum,'Testo mancante o troppo lungo.')
    return value.strip()

def api(path,b,token):
    with connect() as c:
        c.execute('BEGIN IMMEDIATE')
        if path in ('/api/create','/api/join'):
            name=label(b.get('name'))
            if path.endswith('create'):
                code=''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
                c.execute('INSERT INTO sessions(code,name) VALUES(?,?)',(code,label(b.get('session')))); role='Master'
            else:
                code=str(b.get('code','')).strip().upper(); role='Giocatore'
                require(c.execute('SELECT 1 FROM sessions WHERE code=?',(code,)).fetchone(),'Codice sessione non trovato.',404)
            require(c.execute('SELECT phase FROM sessions WHERE code=?',(code,)).fetchone()[0]=='Preparazione','La partita è iniziata. Chiedi al Master di riaprire la preparazione.')
            require(not c.execute('SELECT 1 FROM members WHERE code=? AND name=?',(code,name)).fetchone(),'Nome già usato: scegline un altro.')
            mid=secrets.token_hex(12); tok=secrets.token_urlsafe(32)
            c.execute('INSERT INTO members VALUES(?,?,?,?,?)',(mid,code,name,role,tok))
            if role=='Giocatore': c.execute('INSERT INTO sheets(owner,data,version) VALUES(?,?,1)',(mid,json.dumps(initial())))
            event(c,code,mid,name,'Ingresso',{})
            return {'token':tok}
        m=c.execute('SELECT * FROM members WHERE token=?',(token,)).fetchone()
        require(m is not None,'Accesso non valido. Rientra nella sessione.',401)
        code=m['code']
        if path=='/api/state':
            members=[dict(x) for x in c.execute('SELECT id,name,role FROM members WHERE code=?',(code,))]
            sheets=[]
            for x in c.execute('SELECT s.* FROM sheets s JOIN members m ON m.id=s.owner WHERE m.code=?',(code,)):
                if m['role']=='Master' or x['owner']==m['id']: sheets.append({'owner':x['owner'],'version':x['version'],'ready':bool(x['ready']),'data':json.loads(x['data'])})
            events=[]
            for x in c.execute('SELECT * FROM events WHERE code=? ORDER BY id DESC',(code,)):
                if m['role']=='Master' or x['owner']==m['id']:
                    e=dict(x);e['changes']=json.loads(e['changes']);events.append(e)
            return {'me':dict(id=m['id'],name=m['name'],role=m['role']), 'code':code, 'name':c.execute('SELECT name FROM sessions WHERE code=?',(code,)).fetchone()[0], 'phase':c.execute('SELECT phase FROM sessions WHERE code=?',(code,)).fetchone()[0], 'members':members,'sheets':sheets,'events':events,'fields':FIELDS}
        if path=='/api/phase':
            require(m['role']=='Master','Solo il Master avvia la partita.',403)
            phase=b.get('phase'); require(phase in ('Preparazione','In gioco'),'Fase non valida.')
            if phase=='In gioco':
                rows=c.execute('SELECT s.ready FROM sheets s JOIN members m ON m.id=s.owner WHERE m.code=?',(code,)).fetchall()
                require(rows and all(r['ready'] for r in rows),'Serve almeno un giocatore e tutte le schede devono essere confermate.')
            c.execute('UPDATE sessions SET phase=? WHERE code=?',(phase,code))
            event(c,code,m['id'],m['name'],phase,{},'Cambio fase della sessione')
            return {'ok':True}
        require(path=='/api/edit','Operazione non trovata.',404)
        owner=b.get('owner'); sheet=c.execute('SELECT s.* FROM sheets s JOIN members m ON m.id=s.owner WHERE s.owner=? AND m.code=?',(owner,code)).fetchone()
        require(sheet is not None,'Scheda non trovata.',404)
        require(m['role']=='Master' or owner==m['id'],'Puoi modificare soltanto le tue schede.',403)
        require(type(b.get('version')) is int and b['version']==sheet['version'],'La scheda è cambiata: ricarica i dati prima di salvare. La tua bozza resta visibile.',409)
        patch=b.get('patch'); require(isinstance(patch,dict),'Richiesta non valida.')
        confirm=b.get('confirm') is True
        require(patch or confirm,'Nessuna modifica.')
        reason=label(b.get('reason',''),500) if m['role']=='Master' else ''
        data=json.loads(sheet['data']); changes={}
        for k,v in patch.items():
            require(k in FIELDS,'Campo non consentito.')
            f=FIELDS[k]
            if f[1]=='text': require(isinstance(v,str) and len(v)<=4000,'Testo troppo lungo.')
            else: require(type(v) is int and f[2]<=v<=f[3],f'{f[0]}: valore consentito {f[2]}–{f[3]}.')
            if data[k]!=v: changes[k]={'prima':data[k],'dopo':v};data[k]=v
        require(data['HP umano']<=5+data['COS'],'HP umani oltre il massimo (5 + Costituzione). Aggiorna anche gli HP se riduci COS.')
        for a,z in [('ARM','ARM max'),('EN','EN max'),('HP mecha','HP max mecha')]: require(data[a]<=data[z],f'{a} supera il massimo.')
        if confirm:
            require(data['personaggio'].strip() and data['personaggio']!='Nuovo personaggio','Scegli il nome del personaggio.')
            require(data['mecha'].strip() and data['mecha']!='Da configurare','Indica il nome o modello del mecha concordato con il Master.')
            require(b.get('agreed') is True,'Conferma di aver concordato i valori con il Master.')
        require(changes or confirm,'Nessun valore è cambiato.')
        c.execute('UPDATE sheets SET data=?,version=version+1 WHERE owner=?',(json.dumps(data),owner))
        if confirm: c.execute('UPDATE sheets SET ready=1 WHERE owner=?',(owner,))
        event(c,code,owner,m['name'],'Scheda confermata' if confirm else 'Correzione Master' if m['role']=='Master' else 'Modifica',changes,reason)
        return {'ok':True}

class Handler(BaseHTTPRequestHandler):
    def reply(self,status,obj,content='application/json'):
        raw=json.dumps(obj).encode() if content=='application/json' else obj
        self.send_response(status);self.send_header('Content-Type',content+'; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    def do_GET(self):
        if self.path.split('?')[0] in ('/','/index.html'): self.reply(200,(ROOT/'index.html').read_bytes(),'text/html')
        elif self.path.split('?')[0]=='/assets/prism-hangar.webp': self.reply(200,(ROOT/'assets/prism-hangar.webp').read_bytes(),'image/webp')
        else: self.reply(404,{'error':'Non trovato'})
    def do_POST(self):
        try:
            origin=self.headers.get('Origin')
            require(not origin or origin in ('http://'+self.headers.get('Host',''),'https://'+self.headers.get('Host','')),'Origine non consentita.',403)
            n=int(self.headers.get('Content-Length','0'));require(0<n<=64000,'Richiesta troppo grande.')
            b=json.loads(self.rfile.read(n));require(isinstance(b,dict),'Richiesta non valida.')
            self.reply(200,api(self.path,b,self.headers.get('Authorization','').removeprefix('Bearer ')))
        except Problem as e: self.reply(e.status,{'error':e.msg})
        except (ValueError,TypeError): self.reply(400,{'error':'Richiesta non valida.'})
        except Exception: self.reply(500,{'error':'Errore interno. Nessuna modifica confermata.'})
    def log_message(self,*args): pass
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=8765);a=p.parse_args();init()
    print(f'PRISM Companion: http://{a.host}:{a.port}',flush=True)
    ThreadingHTTPServer((a.host,a.port),Handler).serve_forever()
