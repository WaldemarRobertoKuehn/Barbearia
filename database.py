import json, sqlite3, sys

DB = 'norden.sqlite'
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
conn.execute('PRAGMA foreign_keys=ON')
conn.executescript('''
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, role TEXT NOT NULL DEFAULT 'client', phone TEXT DEFAULT '', allergies TEXT DEFAULT '', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS services(id INTEGER PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL, price INTEGER NOT NULL, duration INTEGER NOT NULL, active INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS professionals(id INTEGER PRIMARY KEY, name TEXT NOT NULL, specialty TEXT NOT NULL, active INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL, description TEXT NOT NULL, price INTEGER NOT NULL, stock INTEGER NOT NULL DEFAULT 0, active INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS appointments(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), service_id INTEGER NOT NULL REFERENCES services(id), professional_id INTEGER NOT NULL REFERENCES professionals(id), starts_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'confirmed', notes TEXT DEFAULT '', care TEXT DEFAULT '', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS appointment_products(appointment_id INTEGER REFERENCES appointments(id), product_id INTEGER REFERENCES products(id), PRIMARY KEY(appointment_id,product_id));
CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), fulfillment TEXT NOT NULL, address TEXT DEFAULT '', distance_km REAL DEFAULT 0, fee INTEGER DEFAULT 0, total INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'received', payment_method TEXT NOT NULL DEFAULT 'presencial', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS order_items(id INTEGER PRIMARY KEY, order_id INTEGER REFERENCES orders(id), product_id INTEGER REFERENCES products(id), quantity INTEGER NOT NULL, unit_price INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS offers(id INTEGER PRIMARY KEY, appointment_id INTEGER REFERENCES appointments(id), offered_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, actor_id INTEGER, action TEXT, entity TEXT, entity_id INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
''')
if conn.execute('SELECT count(*) FROM services').fetchone()[0] == 0:
    conn.executemany('INSERT INTO services(name,description,price,duration) VALUES(?,?,?,?)', [
      ('Corte clássico','Corte personalizado com acabamento à navalha.',7500,45),('Barba & contorno','Toalha quente, desenho e finalização.',5500,30),('Corte + barba','Experiência completa de cabelo e barba.',11000,75),('Camuflagem capilar','Disfarce natural de fios brancos.',8500,45)])
    conn.executemany('INSERT INTO professionals(name,specialty) VALUES(?,?)',[('Rafael Almeida','Corte e visagismo'),('Caio Mendes','Barba e tratamentos')])
    conn.executemany('INSERT INTO products(name,category,description,price,stock) VALUES(?,?,?,?,?)',[
      ('Pomada Matte Norden','Finalização','Fixação natural, acabamento sem brilho.',8900,12),('Óleo de Barba','Barba','Blend nutritivo para barba e pele.',6900,8),('Shampoo Purificante','Cabelo','Limpeza suave para uso frequente.',5900,15),('Pente de Madeira','Acessórios','Pente de bolso com dentes largos.',3900,6)])
    conn.execute("INSERT INTO users(name,email,role,phone) VALUES('Lucas Martins','lucas@norden.demo','client','(11) 99999-1000')")
    conn.execute("INSERT INTO users(name,email,role,phone) VALUES('Rafael Almeida','rafael@norden.demo','admin','(11) 99999-2000')")
    conn.commit()

def rows(sql, args=()): return [dict(r) for r in conn.execute(sql,args).fetchall()]
def one(sql,args=()):
    r=conn.execute(sql,args).fetchone(); return dict(r) if r else None
def audit(actor, action, entity, eid=None): conn.execute('INSERT INTO audit(actor_id,action,entity,entity_id) VALUES(?,?,?,?)',(actor,action,entity,eid))
def run(op, d):
    if op=='init': return {'services':rows('SELECT * FROM services WHERE active=1'),'professionals':rows('SELECT * FROM professionals WHERE active=1'),'products':rows('SELECT * FROM products WHERE active=1'),'users':rows('SELECT id,name,email,role FROM users'),'appointments':rows('''SELECT a.*,u.name client,s.name service,s.price,s.duration,p.name professional FROM appointments a JOIN users u ON u.id=a.user_id JOIN services s ON s.id=a.service_id JOIN professionals p ON p.id=a.professional_id ORDER BY a.starts_at'''),'orders':rows('''SELECT o.*,u.name client FROM orders o JOIN users u ON u.id=o.user_id ORDER BY o.created_at DESC'''),'offers':rows('''SELECT f.*,u.name client,s.name service,a.starts_at FROM offers f JOIN appointments a ON a.id=f.appointment_id JOIN users u ON u.id=a.user_id JOIN services s ON s.id=a.service_id ORDER BY f.created_at DESC'''),'audit':rows('SELECT * FROM audit ORDER BY id DESC LIMIT 30')}
    if op=='register':
        cur=conn.execute('INSERT INTO users(name,email,phone) VALUES(?,?,?)',(d['name'],d['email'].lower(),d.get('phone',''))); audit(cur.lastrowid,'cadastro','user',cur.lastrowid); conn.commit(); return one('SELECT id,name,email,role FROM users WHERE id=?',(cur.lastrowid,))
    if op=='book':
        svc=one('SELECT * FROM services WHERE id=? AND active=1',(d['service_id'],))
        if not svc: raise ValueError('Serviço indisponível.')
        start=d['starts_at']; end=__import__('datetime').datetime.fromisoformat(start)+__import__('datetime').timedelta(minutes=svc['duration'])
        conflicts=conn.execute("SELECT a.starts_at,s.duration FROM appointments a JOIN services s ON s.id=a.service_id WHERE a.professional_id=? AND a.status IN ('confirmed','in_progress')",(d['professional_id'],)).fetchall()
        for c in conflicts:
            cs=__import__('datetime').datetime.fromisoformat(c['starts_at']); ce=cs+__import__('datetime').timedelta(minutes=c['duration'])
            if cs < end and __import__('datetime').datetime.fromisoformat(start) < ce: raise ValueError('Este horário acabou de ser ocupado. Escolha outro.')
        cur=conn.execute('INSERT INTO appointments(user_id,service_id,professional_id,starts_at,notes) VALUES(?,?,?,?,?)',(d['user_id'],d['service_id'],d['professional_id'],start,d.get('notes',''))); audit(d['user_id'],'agendamento criado','appointment',cur.lastrowid); conn.commit(); return {'id':cur.lastrowid}
    if op=='cancel':
        a=one('SELECT * FROM appointments WHERE id=?',(d['id'],))
        if not a or (d['role']!='admin' and a['user_id']!=d['actor']): raise PermissionError('Agendamento não encontrado ou sem permissão.')
        if a['status']!='confirmed': raise ValueError('Este agendamento não pode ser cancelado agora.')
        conn.execute("UPDATE appointments SET status='cancelled' WHERE id=?",(d['id'],)); audit(d['actor'],'agendamento cancelado','appointment',d['id'])
        future=rows("SELECT a.id,a.starts_at,s.duration FROM appointments a JOIN services s ON s.id=a.service_id WHERE a.status='confirmed' AND a.starts_at>? ORDER BY a.starts_at",(a['starts_at'],))
        slot=__import__('datetime').datetime.fromisoformat(a['starts_at']); offers=[]
        for candidate in future:
            if candidate['duration'] <= 60:
                cur=conn.execute('INSERT INTO offers(appointment_id,offered_at) VALUES(?,?)',(candidate['id'],slot.isoformat(timespec='minutes'))); offers.append(cur.lastrowid); break
        conn.commit(); return {'cancelled':True,'offers':len(offers)}
    if op=='offer':
        f=one('SELECT f.*,a.user_id FROM offers f JOIN appointments a ON a.id=f.appointment_id WHERE f.id=?',(d['id'],))
        if not f or (d['role']!='admin' and f['user_id']!=d['actor']): raise PermissionError('Oferta não encontrada ou sem permissão.')
        conn.execute('UPDATE offers SET status=? WHERE id=?',('accepted' if d['accept'] else 'declined',d['id']))
        if d['accept']: conn.execute('UPDATE appointments SET starts_at=? WHERE id=?',(f['offered_at'],f['appointment_id']))
        audit(d['actor'],'oferta '+('aceita' if d['accept'] else 'recusada'),'offer',d['id']); conn.commit(); return {'ok':True}
    if op=='complete':
        if d['role']!='admin': raise PermissionError('Apenas a equipe pode concluir atendimentos.')
        ids=d.get('products',[]); a=one('SELECT * FROM appointments WHERE id=?',(d['id'],))
        if not a or a['status'] not in ('confirmed','in_progress'): raise ValueError('Atendimento indisponível.')
        for pid in ids: conn.execute('INSERT OR IGNORE INTO appointment_products VALUES(?,?)',(d['id'],pid))
        conn.execute("UPDATE appointments SET status='completed',care=? WHERE id=?",(d.get('care',''),d['id'])); audit(d['actor'],'atendimento concluído','appointment',d['id']); conn.commit(); return {'ok':True}
    if op=='order':
        items=d.get('items',[])
        if not items: raise ValueError('Seu carrinho está vazio.')
        conn.execute('BEGIN IMMEDIATE'); total=0; clean=[]
        for item in items:
            p=one('SELECT * FROM products WHERE id=? AND active=1',(item['product_id'],)); q=int(item['quantity'])
            if not p or q<1 or q>p['stock']: raise ValueError('Estoque insuficiente para um dos itens.')
            total+=p['price']*q; clean.append((p,q))
        fee=round(float(d.get('distance_km',0))*250) if d.get('fulfillment')=='delivery' else 0
        total+=fee
        cur=conn.execute('INSERT INTO orders(user_id,fulfillment,address,distance_km,fee,total,payment_method) VALUES(?,?,?,?,?,?,?)',(d['user_id'],d['fulfillment'],d.get('address',''),float(d.get('distance_km',0)),fee,total,d.get('payment_method','presencial')))
        for p,q in clean:
            conn.execute('INSERT INTO order_items(order_id,product_id,quantity,unit_price) VALUES(?,?,?,?)',(cur.lastrowid,p['id'],q,p['price'])); conn.execute('UPDATE products SET stock=stock-? WHERE id=?',(q,p['id']))
        audit(d['user_id'],'pedido criado','order',cur.lastrowid); conn.commit(); return {'id':cur.lastrowid,'total':total,'fee':fee}
    if op=='order_status':
        if d['role']!='admin': raise PermissionError('Apenas a equipe pode atualizar pedidos.')
        if d['status'] not in ('preparing','ready','completed','cancelled'): raise ValueError('Status inválido.')
        conn.execute('UPDATE orders SET status=? WHERE id=?',(d['status'],d['id'])); audit(d['actor'],'pedido atualizado','order',d['id']); conn.commit(); return {'ok':True}
    if op=='profile':
        conn.execute('UPDATE users SET phone=?,allergies=? WHERE id=? AND role="client"',(d.get('phone',''),d.get('allergies',''),d['actor'])); conn.commit(); return {'ok':True}
    raise ValueError('Operação desconhecida.')

try:
    data=json.load(sys.stdin); result=run(data['op'],data.get('data',{})); print(json.dumps({'ok':True,'data':result},ensure_ascii=False))
except Exception as e:
    conn.rollback(); print(json.dumps({'ok':False,'error':str(e),'kind':type(e).__name__},ensure_ascii=False))
finally: conn.close()
