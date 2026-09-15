// Isolated headless browser; never attaches to the owner's logged-in browser.
const {chromium} = require(process.env.PLAYWRIGHT_MODULE);
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const root = path.resolve(__dirname, '..');
const base = process.env.RAZVITON_TEST_BASE || 'http://127.0.0.1:8019';
if (!['127.0.0.1','localhost'].includes(new URL(base).hostname)) throw Error('LOCAL_ONLY');
const out = path.join(root, 'audit_artifacts');
fs.mkdirSync(out, {recursive:true});
(async()=>{
 const browser = await chromium.launch({headless:true, executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
 const tests = [], errors = [];
 const check=(name,ok,evidence='')=>tests.push({name,status:ok?'PASS':'FAIL',evidence});
 try {
 for (const [label,width,height] of [['desktop',1440,1000],['mobile',390,844]]) {
  const context = await browser.newContext({viewport:{width,height}});
  const page = await context.newPage();
  page.on('pageerror', e=>errors.push({layout:label,error:e.message}));
  page.on('response', r=>{if(r.status()>=400 && ![401,403].includes(r.status()))errors.push({layout:label,url:r.url(),status:r.status()});});
  for (const file of fs.readdirSync(path.join(root,'public')).filter(x=>x.endsWith('.html'))) {
   await page.goto(base+'/'+file,{waitUntil:'networkidle'});
   check(`${label}:${file}:heading`,await page.locator('h1').count()===1);
   const overflow = await page.evaluate(()=>Array.from(document.querySelectorAll('main, .auth-shell, .nav, .card, .box')).filter(e=>{const r=e.getBoundingClientRect();return r.right>innerWidth+2 || r.left < -2}).length);
   check(`${label}:${file}:overflow`,overflow===0,String(overflow));
  }
  await page.goto(base,{waitUntil:'networkidle'});
  if(label==='mobile'){
   await page.locator('.mobile-menu-btn').click();
   check('mobile:menu_open',await page.locator('.mobile-menu-btn').getAttribute('aria-expanded')==='true');
   await page.keyboard.press('Escape');
   check('mobile:menu_escape',await page.locator('.mobile-menu-btn').getAttribute('aria-expanded')==='false');
  }
  await page.screenshot({path:path.join(out,`${label}-home.png`),fullPage:true});
  await context.close();
 }
 const context = await browser.newContext();
 const page = await context.newPage();
 const id='browser'+Date.now();
 const testPassword=crypto.randomBytes(24).toString('base64url');
 await page.goto(base+'/register.html',{waitUntil:'networkidle'});
 await page.locator('[name=username]').fill(id);
 await page.locator('[name=email]').fill(id+'@example.invalid');
 await page.locator('[name=password]').fill(testPassword);
 await page.locator('button[type=submit]').click();
 await page.waitForURL('**/account.html');
 await page.waitForFunction(()=>document.querySelector('#account-me').textContent.includes('@example.invalid'));
 check('browser:register_and_account',true);
 await page.locator('#auth-logout').click(); await page.waitForURL('**/index.html');
 check('browser:logout',true);
 await page.goto(base+'/login.html',{waitUntil:'networkidle'});
 await page.locator('[name=identifier]').fill(id.toUpperCase());
 await page.locator('[name=password]').fill(testPassword);
 await page.locator('button[type=submit]').click(); await page.waitForURL('**/account.html');
 check('browser:login',true);
 await page.goto(base+'/admin.html',{waitUntil:'networkidle'});
 check('browser:admin_denied',!(await page.locator('#admin-stats').textContent()).includes('Loading...'));
 await context.close();
 check('browser:no_unexpected_errors',errors.length===0,JSON.stringify(errors));
 }catch(e){check('browser:exception',false,e.message);}finally{await browser.close();}
 fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify({timestamp:new Date().toISOString(),tests,errors},null,2));
 console.log(JSON.stringify({pass:tests.filter(t=>t.status==='PASS').length,fail:tests.filter(t=>t.status==='FAIL').length,failures:tests.filter(t=>t.status==='FAIL')}));
 process.exitCode=tests.some(t=>t.status==='FAIL')?1:0;
})();
