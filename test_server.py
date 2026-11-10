"""Test d'integrazione: database temporaneo, nessun dato reale modificato."""
import unittest, tempfile, threading, urllib.request, urllib.error, json
import server
class Multiplayer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();server.DB=cls.tmp.name+'/test.sqlite3';server.init()
        cls.http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        cls.url='http://127.0.0.1:'+str(cls.http.server_port)
        threading.Thread(target=cls.http.serve_forever,daemon=True).start()
    @classmethod
    def tearDownClass(cls): cls.http.shutdown();cls.http.server_close();cls.tmp.cleanup()
    def req(self,path,b=None,t='',status=200):
        req=urllib.request.Request(self.url+'/api/'+path,data=json.dumps(b or {}).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+t})
        try:r=urllib.request.urlopen(req)
        except urllib.error.HTTPError as e:r=e
        self.assertEqual(r.status,status);return json.load(r)
    def test_complete_flow(self):
        master=self.req('create',{'name':'Master','session':'Test'})['token'];state=self.req('state',t=master);code=state['code']
        self.req('join',{'name':'No','code':'INVALID'},status=404)
        a=self.req('join',{'name':'A','code':code})['token'];b=self.req('join',{'name':'B','code':code})['token']
        self.req('join',{'name':'A','code':code},status=400)
        sa=self.req('state',t=a);owner=sa['me']['id'];sb=self.req('state',t=b)
        self.assertEqual(len(self.req('state',t=master)['sheets']),2);self.assertEqual(len(sa['sheets']),1)
        self.req('edit',{'owner':owner,'version':1,'patch':{'HP umano':12}},t=b,status=403)
        self.req('state',t='fake',status=401)
        self.req('edit',{'owner':owner,'version':1,'patch':{'SEN':51}},t=a,status=400)
        self.req('edit',{'owner':owner,'version':1,'patch':{'COS':0}},t=a,status=400)
        self.req('edit',{'owner':owner,'version':1,'patch':{'HP umano':16}},t=a,status=400)
        self.req('edit',{'owner':owner,'version':1,'patch':{'ARM':1}},t=a,status=400)
        self.req('edit',{'owner':owner,'version':1,'patch':{'HP umano':-2,'SEN':50}},t=a)
        self.req('edit',{'owner':owner,'version':1,'patch':{'HP umano':10},'reason':'Vecchia versione'},t=master,status=409)
        self.req('edit',{'owner':owner,'version':2,'patch':{'HP umano':10}},t=master,status=400)
        self.req('edit',{'owner':owner,'version':2,'patch':{'HP umano':10},'reason':'Correzione'},t=master)
        s=self.req('state',t=a);self.assertEqual(s['sheets'][0]['data']['HP umano'],10);self.assertEqual(s['events'][0]['actor'],'Master')
        self.assertEqual(s['events'][0]['changes']['HP umano'],{'prima':-2,'dopo':10})
        self.assertFalse(any(e['owner']==owner for e in self.req('state',t=b)['events']))
        self.req('edit',{'owner':owner,'version':3,'patch':{'HP umano':-2},'reason':'Ripristino'},t=master)
        self.assertEqual(self.req('state',t=a)['sheets'][0]['data']['HP umano'],-2)
        # Due salvataggi simultanei: esattamente uno può usare revisione 4.
        import concurrent.futures
        def race(v):
            try:return server.api('/api/edit',{'owner':owner,'version':4,'patch':{'HP umano':v}},a)
            except server.Problem as e:return e.status
        with concurrent.futures.ThreadPoolExecutor() as ex: results=list(ex.map(race,[1,2]))
        self.assertEqual(sum(x==409 for x in results),1)
        # Riapertura database: i dati e l'accesso restano persistenti.
        server.init();self.assertEqual(self.req('state',t=a)['sheets'][0]['version'],5)
        foreign=self.req('create',{'name':'Altro master','session':'Altra'})['token']
        self.req('edit',{'owner':owner,'version':5,'patch':{'HP umano':5},'reason':'No'},t=foreign,status=404)
        self.assertEqual(self.req('state',t=b)['sheets'][0]['owner'],sb['me']['id'])
    def test_setup_and_phase(self):
        master=self.req('create',{'name':'M','session':'Configurazione'})['token']
        code=self.req('state',t=master)['code']
        self.req('phase',{'phase':'In gioco'},t=master,status=400)
        player=self.req('join',{'name':'P','code':code})['token']
        state=self.req('state',t=player);owner=state['me']['id']
        self.assertFalse(state['sheets'][0]['ready'])
        self.req('phase',{'phase':'In gioco'},t=player,status=403)
        self.req('phase',{'phase':'In gioco'},t=master,status=400)
        self.req('edit',{'owner':owner,'version':1,'patch':{},'confirm':True,'agreed':True},t=player,status=400)
        names={'personaggio':'Nova','mecha':'Atlas'}
        self.req('edit',{'owner':owner,'version':1,'patch':names,'confirm':True},t=player,status=400)
        self.req('edit',{'owner':owner,'version':1,'patch':names},t=player)
        self.assertFalse(self.req('state',t=player)['sheets'][0]['ready'])
        self.req('edit',{'owner':owner,'version':2,'patch':{},'confirm':True,'agreed':True},t=player)
        self.assertTrue(self.req('state',t=master)['sheets'][0]['ready'])
        self.req('phase',{'phase':'In gioco'},t=master)
        self.assertEqual(self.req('state',t=player)['phase'],'In gioco')
        self.req('join',{'name':'Ritardatario','code':code},status=400)
        self.req('phase',{'phase':'Preparazione'},t=master)
        self.req('join',{'name':'Ritardatario','code':code})
        self.req('phase',{'phase':'In gioco'},t=master,status=400)

if __name__=='__main__':unittest.main(verbosity=2)
