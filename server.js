const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const { spawn } = require('node:child_process');
const root = __dirname;
const mime = {'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg'};
function db(op,data={}) { return new Promise((resolve,reject)=>{ const p=spawn('python',['-X','utf8','database.py'],{cwd:root,env:{...process.env,PYTHONUTF8:'1',PYTHONIOENCODING:'utf-8'}}); let out=''; p.stdout.setEncoding('utf8'); p.stdout.on('data',d=>out+=d); p.stderr.on('data',d=>{}); p.on('close',()=>{try{const r=JSON.parse(out);r.ok?resolve(r.data):reject(Object.assign(new Error(r.error),{status:r.kind==='PermissionError'?403:r.kind==='ValueError'?400:500}));}catch{reject(new Error('Falha ao acessar o banco local.'));}}); p.stdin.end(JSON.stringify({op,data}), 'utf8'); }); }
http.createServer(async(req,res)=>{
  const url=new URL(req.url,'http://localhost');
  if(url.pathname.startsWith('/api/')) { res.setHeader('Content-Type','application/json; charset=utf-8'); res.setHeader('Cache-Control','no-store'); try {let body={}; if(req.method==='POST'){let raw='';for await(const c of req)raw+=c;body=JSON.parse(raw||'{}');} const result=await db(url.pathname.slice(5),body);res.end(JSON.stringify({ok:true,data:result}));}catch(e){res.statusCode=e.status||500;res.end(JSON.stringify({ok:false,error:e.message}));} return; }
  let file=path.join(root,url.pathname==='/'?'index.html':decodeURIComponent(url.pathname));if(!file.startsWith(root)){res.statusCode=403;res.end();return;} if(!fs.existsSync(file)||fs.statSync(file).isDirectory())file=path.join(root,'index.html');res.setHeader('Content-Type',mime[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);
}).listen(process.env.PORT||4173,'127.0.0.1',()=>console.log('NORDEN MVP em http://localhost:'+(process.env.PORT||4173)));
